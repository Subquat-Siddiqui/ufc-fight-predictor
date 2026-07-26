"""
This file will contain necessary logic for when a user tries to predict a matchup between 2 fighters.
The logic includes retrieving the latest fighter stats, retrieving live betting odds, and then predicting the winner.
"""
from pathlib import Path
import pandas as pd
import joblib
import requests
import os
from dotenv import load_dotenv

load_dotenv() # For retrieving api key responsible for querying fight odds

# MUST have run ml_core\notebooks\03_final_model_export.ipynb in order retrieve already pre-trained model
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "ml_core" / "models" / "trained_model.joblib"
COLUMNS_PATH = PROJECT_ROOT / "ml_core" / "models" / "feature_columns.joblib"
model = joblib.load(filename=MODEL_PATH)
feature_columns = joblib.load(COLUMNS_PATH)

# Retrieving processed training dataset as a dataframe
# Build the data path to where processed training data source is located (ufc-master-processed.csv)
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "ufc-master-processed.csv"
df = pd.read_csv(DATA_PATH)


def get_fighter_stats(fighter_name: str) -> dict:
    """
    Queries and returns the stats of the specified fighter based on their latest recorded fight.
    Will throw an error if specified history wasn't found.

    Args:
        fighter_name (str): Name of fighter

    Returns:
        a dict of fighter data, from their latest fight
    """
    fighter_name = fighter_name.lower() # Not case-sensitive

    # Sort by newest fights, then query for the specified fighters latest fight
    df_fighter = df.sort_values(by="Date", ascending=False)
    df_fighter = df_fighter[(df_fighter["RedFighter"].str.lower() == fighter_name) | (df_fighter["BlueFighter"].str.lower() == fighter_name)].head(1)

    # Will drop the following columns as they're not specific only to the fighter we're querying for
    # Certain columns dropped here will be rebuilt once we have data from both fighters using build_feature_row
    df_fighter = df_fighter.drop(columns=["LoseStreakDif", "WinStreakDif", "LongestWinStreakDif", "WinDif", "LossDif", 
                                      "TotalRoundDif", "TotalTitleBoutDif", "KODif", "SubDif", "HeightDif", "ReachDif", 
                                      "AgeDif", "SigStrDif", "AvgSubAttDif", "AvgTDDif", "Date", "NumberOfRounds", 
                                      "TitleBout_Encoded", "WeightClass_Encoded", "BetterRank_Encoded",
                                      "Winner_Encoded", "RedOdds", "BlueOdds", "RedExpectedValue", "BlueExpectedValue"])

    # No fighter history
    if df_fighter.empty:
        raise ValueError(f"No fight history for {fighter_name}")

    if df_fighter["RedFighter"].iloc[0].lower() == fighter_name:
        cols_to_drop = df_fighter.filter(regex='(?i)blue').columns # Columns containing data for opposing fighter
        df_fighter = df_fighter.drop(columns=cols_to_drop) # Keeping only columns pertaining to specified fighter

        # Now drop the ranks of the fighter they were facing, so we're left only with the ranks of the RedFighter
        blue_rank_cols = ["BWFlyweightRank", "BWFeatherweightRank", "BWStrawweightRank", "BWBantamweightRank", 
                   "BHeavyweightRank", "BLightHeavyweightRank", "BMiddleweightRank", "BWelterweightRank", 
                   "BLightweightRank", "BFeatherweightRank", "BBantamweightRank", "BFlyweightRank", "BPFPRank",
                    "BMatchWCRank"]
        df_fighter = df_fighter.drop(columns=blue_rank_cols) 

    else:
        # Same logic, but if queried fighter turned out to be BlueFighter
        cols_to_drop = df_fighter.filter(regex='(?i)red').columns
        df_fighter = df_fighter.drop(columns=cols_to_drop)

        # Now drop the ranks of the fighter they were facing, so we're left only with the ranks of the BlueFighter
        red_rank_cols = ["RWFlyweightRank", "RWFeatherweightRank", "RWStrawweightRank", "RWBantamweightRank", 
                  "RHeavyweightRank", "RLightHeavyweightRank", "RMiddleweightRank", "RWelterweightRank", 
                  "RLightweightRank", "RFeatherweightRank", "RBantamweightRank", "RFlyweightRank", "RPFPRank", 
                  "RMatchWCRank"]
        df_fighter = df_fighter.drop(columns=red_rank_cols)

    return df_fighter.iloc[0].to_dict()


def reassign_corner(stats: dict, target_corner: str) -> dict:
    """
    Renames a fighter's stat dict keys so they reflect the specified corner
    (Red or Blue), regardless of which corner they originally fought from.
    Handles both full-word prefixes (RedWins, BlueAge) and single-letter
    rank-column prefixes (RMatchWCRank, BPFPRank).

    Args:
        stats (dict): fighter stats
        target_corner (str): Red or Blue
    Returns:
        Renamed values labeling the fighter to be in either the Red corner or the Blue corner
    """
    current_full = "Red" if "RedFighter" in stats else "Blue"
    current_single = current_full[0]  # "R" or "B"
    target_single = target_corner[0]

    renamed = {}
    for key, value in stats.items():
        if key.startswith(current_full):
            new_key = target_corner + key[len(current_full):]
        elif key.startswith(current_single):
            new_key = target_single + key[len(current_single):]
        else:
            new_key = key  # shouldn't happen, but keeps unexpected keys intact
        renamed[new_key] = value

    return renamed

def get_live_odds(fighter_a: str, fighter_b: str) -> dict:
    """
    Will retrieve upcoming odds of an upcoming match between the specified fighters.
    The fighters must be having an upcoming match, odds can't be retrieved for hypothetical 
    fights or ones that haven't been scheduled.

    Args:
        fighter_a (str): Name of first fighter
        fighter_b (str): Name of second fighter
    Returns:
        A dict containing odds for each specified fighter
    """
    # Ensure fighter names aren't case sensitive
    fighter_a = fighter_a.lower()
    fighter_b = fighter_b.lower()

    odds = {}

    url = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds"

    # Specify region, markets, and format with the request
    response = requests.get(url, params={
       "regions": "us",
       "markets": "h2h",
       "oddsFormat": "american",
       "apiKey": os.getenv("ODDS_API_KEY")
   })

    if response.status_code != 200:
        raise ValueError(f"API request failed with status: {response.status_code}")

    # obtain a list of dicts containing confirmed fiht odds for all upcoming scheduled fights
    fights = response.json()

    # Look for the upcoming specified fight, where either fighter can be home or away
    for fight in fights:
        # Correct fight found
        if (
            fight["home_team"].lower() == fighter_a and fight["away_team"].lower() == fighter_b
            or
            fight["home_team"].lower() == fighter_b and fight["away_team"].lower() == fighter_a
        ):
            bookmaker = fight["bookmakers"][0] # Grab the first bookmaker

            # Find the h2h (moneyline) market within the bookmaker
            h2h_market = None
            for market in bookmaker["markets"]:
                if market["key"] == "h2h":
                    h2h_market = market
                    break

            if h2h_market is None:
                raise ValueError(f"No h2h market found for {fighter_a} and {fighter_b}")

            # Match each outcome's price back to the correct fighter
            for outcome in h2h_market["outcomes"]:
                name = outcome["name"].lower()
                if name == fighter_a:
                    odds[fighter_a] = outcome["price"]
                elif name == fighter_b:
                    odds[fighter_b] = outcome["price"]

            break  # found our fight, stop looping

    # If matching fight never found        
    if len(odds) != 2:
        raise ValueError(f"No scheduled fight found for {fighter_a} and {fighter_b}")
        
    return odds


def odds_to_expected_value(odds: float) -> float:
    """Converts American odds to expected value (payout per $100 bet)."""
    return odds if odds > 0 else 10000 / abs(odds)


def build_feature_row(fighter_a: str, fighter_b: str, weight_class_encoded: int,
                       title_bout: bool, num_rounds: int) -> pd.DataFrame:
    """
    Combines the stats and odds of both fighters into one row, encoded in the same way
    as done in notebook 1.

    Args:
        fighter_a (str): Name of first fighter in matchup
        fighter_b (str): Name of second fighter in matchup
        weight_class_encoded (int): Encoded weight class of this specific fight
        title_bout (bool): Whether this fight is a title bout
        num_rounds (int): Number of rounds scheduled for this fight
    Returns:
        One row of a pd.DataFrame containing information for both fighters, matching
        the column structure of ufc-master-processed.csv
    """
    fighter_a = fighter_a.lower()
    fighter_b = fighter_b.lower()

    fighter_a_stats = get_fighter_stats(fighter_a)
    fighter_b_stats = get_fighter_stats(fighter_b)

    # Get live odds and use them to decide who's Red (favorite) vs Blue (underdog)
    odds = get_live_odds(fighter_a, fighter_b)

    if odds[fighter_a] <= odds[fighter_b]:
        red_name, blue_name = fighter_a, fighter_b
        red_stats, blue_stats = fighter_a_stats, fighter_b_stats
    else:
        red_name, blue_name = fighter_b, fighter_a
        red_stats, blue_stats = fighter_b_stats, fighter_a_stats

    red_stats = reassign_corner(red_stats, "Red")
    blue_stats = reassign_corner(blue_stats, "Blue")

    # Merge both fighters' stats into one row (Gender_Encoded is shared/duplicated, fine to overwrite)
    row = {**red_stats, **blue_stats}

    # Odds and expected value
    row["RedOdds"] = odds[red_name]
    row["BlueOdds"] = odds[blue_name]
    row["RedExpectedValue"] = odds_to_expected_value(odds[red_name])
    row["BlueExpectedValue"] = odds_to_expected_value(odds[blue_name])

    # Rebuild differential columns (confirmed direction: Blue - Red)
    row["LoseStreakDif"] = row["BlueCurrentLoseStreak"] - row["RedCurrentLoseStreak"]
    row["WinStreakDif"] = row["BlueCurrentWinStreak"] - row["RedCurrentWinStreak"]
    row["LongestWinStreakDif"] = row["BlueLongestWinStreak"] - row["RedLongestWinStreak"]
    row["WinDif"] = row["BlueWins"] - row["RedWins"]
    row["LossDif"] = row["BlueLosses"] - row["RedLosses"]
    row["TotalRoundDif"] = row["BlueTotalRoundsFought"] - row["RedTotalRoundsFought"]
    row["TotalTitleBoutDif"] = row["BlueTotalTitleBouts"] - row["RedTotalTitleBouts"]
    row["KODif"] = row["BlueWinsByKO"] - row["RedWinsByKO"]
    row["SubDif"] = row["BlueWinsBySubmission"] - row["RedWinsBySubmission"]
    row["HeightDif"] = row["BlueHeightCms"] - row["RedHeightCms"]
    row["ReachDif"] = row["BlueReachCms"] - row["RedReachCms"]
    row["AgeDif"] = row["BlueAge"] - row["RedAge"]
    row["SigStrDif"] = row["BlueAvgSigStrLanded"] - row["RedAvgSigStrLanded"]
    row["AvgSubAttDif"] = row["BlueAvgSubAtt"] - row["RedAvgSubAtt"]
    row["AvgTDDif"] = row["BlueAvgTDLanded"] - row["RedAvgTDLanded"]

    # Fight-context columns (not derivable, passed in as parameters)
    row["NumberOfRounds"] = num_rounds
    row["TitleBout_Encoded"] = int(title_bout)
    row["WeightClass_Encoded"] = weight_class_encoded

    # BetterRank_Encoded: 0 = neither, 1 = Red, 2 = Blue (lower MatchWCRank = better)
    if row["RMatchWCRank"] < row["BMatchWCRank"]:
        row["BetterRank_Encoded"] = 1
    elif row["BMatchWCRank"] < row["RMatchWCRank"]:
        row["BetterRank_Encoded"] = 2
    else:
        row["BetterRank_Encoded"] = 0

    row_df = pd.DataFrame([row])[feature_columns]
    corner_mapping = {"Red": red_name, "Blue": blue_name}

    return row_df, corner_mapping


def predict_winner(fighter_a: str, fighter_b: str, weight_class_encoded: int,
                    title_bout: bool, num_rounds: int) -> dict:
    """
    Runs the full prediction pipeline for a matchup between two fighters and
    returns the predicted winner and confidence score.
    """
    row, corner_mapping = build_feature_row(fighter_a, fighter_b, weight_class_encoded, title_bout, num_rounds)

    prediction = model.predict(row)[0]  # 0 = Red, 1 = Blue
    probabilities = model.predict_proba(row)[0]  # [P(Red), P(Blue)]

    predicted_corner = "Red" if prediction == 0 else "Blue"
    winner_name = corner_mapping[predicted_corner]
    confidence = probabilities[prediction]

    return {"winner": winner_name, "confidence": round(float(confidence), 4)}