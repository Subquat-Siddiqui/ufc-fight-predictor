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
from datetime import datetime, timedelta, timezone

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

    # Sort by newest fights, then query for the specified fighters latest fight
    df_fighter = df.sort_values(by="Date", ascending=False)
    df_fighter = df_fighter[(df_fighter["RedFighter"].str.lower() == fighter_name.lower()) | (df_fighter["BlueFighter"].str.lower() == fighter_name.lower())].head(1)

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

    if df_fighter["RedFighter"].iloc[0].lower() == fighter_name.lower():
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

    # obtain a list of dicts containing confirmed fight odds for all upcoming scheduled fights
    fights = response.json()

    # Look for the upcoming specified fight, where either fighter can be home or away
    for fight in fights:
        # Correct fight found
        if (
            fight["home_team"].lower() == fighter_a.lower() and fight["away_team"].lower() == fighter_b.lower()
            or
            fight["home_team"].lower() == fighter_b.lower() and fight["away_team"].lower() == fighter_a.lower()
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
                name = outcome["name"]
                if name.lower() == fighter_a.lower():
                    odds[fighter_a] = outcome["price"]
                elif name.lower() == fighter_b.lower():
                    odds[fighter_b] = outcome["price"]

            break  # found our fight, stop looping

    # If matching fight never found        
    if len(odds) != 2:
        raise ValueError(f"No scheduled fight found for {fighter_a} and {fighter_b}")
        
    return odds

_active_fighters_cache = None  # module-level cache, populated on first use

def get_active_ufc_fighters() -> set:
    """
    Fetches the full UFC fighter directory from Cito API and returns a set of
    lowercase names for fighters currently marked active. Cached in memory
    after the first call, since the roster doesn't change frequently enough
    to justify refetching on every request (and doing so would quickly burn
    through the free tier's monthly quota).
    """
    global _active_fighters_cache
    if _active_fighters_cache is not None:
        return _active_fighters_cache

    active_fighters = set()
    page = 1

    while True:
        response = requests.get(
            "https://api.citoapi.com/api/v1/ufc/fighters",
            params={"page": page, "limit": 100},
            headers={"x-api-key": os.getenv("CITO_API_KEY")}
        )

        if response.status_code != 200:
            raise ValueError(f"Cito API request failed with status: {response.status_code}")

        data = response.json()

        for fighter in data["data"]:
            if fighter.get("isActive"):
                active_fighters.add(fighter["name"].lower())

        if not data["meta"]["hasNextPage"]:
            break
        page += 1

    _active_fighters_cache = active_fighters
    return active_fighters


def get_upcoming_fights() -> list[dict]:
    """
    Retrieves all upcoming MMA fights with confirmed odds, filtered to only
    fights where both fighters are currently active on the UFC roster
    (via Cito API).

    Each fight is tagged with a status: "confirmed" if it's scheduled within
    the next 45 days (likely a real, officially booked UFC card), or "rumored"
    if it's further out (likely speculative odds on a callout or potential
    rematch that hasn't been officially booked yet).

    Returns:
        A list of dicts, each containing fighter_a, fighter_b, commence_time,
        and status ("confirmed" or "rumored") for one upcoming fight.
    """
    url = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds"

    response = requests.get(url, params={
       "regions": "us",
       "markets": "h2h",
       "oddsFormat": "american",
       "apiKey": os.getenv("ODDS_API_KEY")
   })

    if response.status_code != 200:
        raise ValueError(f"API request failed with status: {response.status_code}")

    fights = response.json()

    active_ufc_fighters = get_active_ufc_fighters()

    cutoff = datetime.now(timezone.utc) + timedelta(days=45)

    upcoming_fights = []

    for fight in fights:
        home = fight["home_team"]
        away = fight["away_team"]

        if home.lower() in active_ufc_fighters and away.lower() in active_ufc_fighters:
            commence_time = datetime.fromisoformat(fight["commence_time"].replace("Z", "+00:00"))
            status = "confirmed" if commence_time <= cutoff else "rumored"

            upcoming_fights.append({
                "fighter_a": home,
                "fighter_b": away,
                "commence_time": fight["commence_time"],
                "status": status
            })

    return upcoming_fights


def odds_to_expected_value(odds: float) -> float:
    """Converts American odds to expected value (payout per $100 bet)."""
    return odds if odds > 0 else 10000 / abs(odds)

def implied_probability(odds: float) -> float:
    """Converts American odds to the bookmaker's implied win probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


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

    row_df = pd.DataFrame([row])

    # Fill in any expected columns that didn't get created (e.g. asymmetric one-hot
    # categories like BlueStance_nan having no RedStance_nan counterpart)
    missing_cols = [col for col in feature_columns if col not in row_df.columns]
    for col in missing_cols:
        row_df[col] = 0

    row_df = row_df[feature_columns]
    corner_mapping = {"Red": red_name, "Blue": blue_name}

    return row_df, corner_mapping

def predict_from_odds_only(fighter_a: str, fighter_b: str) -> dict:
    """
    Fallback used when one or both fighters lack historical data in our training
    set (e.g. a recent UFC debut). Predicts based on betting odds implied
    probability alone, since the ML model can't be used without fighter stats.
    """
    odds = get_live_odds(fighter_a, fighter_b)

    winner = fighter_a if odds[fighter_a] <= odds[fighter_b] else fighter_b
    confidence = implied_probability(odds[winner])

    return {
        "winner": winner,
        "confidence": round(confidence, 4),
        "method": "odds_only",
        "note": "One or both fighters don't have enough fight history in our dataset yet, so this prediction is based on betting odds alone, not our trained model."
    }

def predict_winner(fighter_a: str, fighter_b: str, weight_class_encoded: int,
                    title_bout: bool, num_rounds: int) -> dict:
    """
    Runs the full prediction pipeline for a matchup between two fighters and
    returns the predicted winner and confidence score. Falls back to an
    odds-only prediction if either fighter lacks historical data.
    """
    try:
        row, corner_mapping = build_feature_row(fighter_a, fighter_b, weight_class_encoded, title_bout, num_rounds)
    except ValueError as e:
        if "No fight history" in str(e):
            return predict_from_odds_only(fighter_a, fighter_b)
        raise  # re-raise anything else (e.g. no scheduled fight found) unchanged

    prediction = model.predict(row)[0]
    probabilities = model.predict_proba(row)[0]

    predicted_corner = "Red" if prediction == 0 else "Blue"
    winner_name = corner_mapping[predicted_corner]
    confidence = probabilities[prediction]

    return {"winner": winner_name, "confidence": round(float(confidence), 4), "method": "model"}