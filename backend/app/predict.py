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
NOTEBOOK_DIR = Path.cwd()  # This is /.../ml_core/models/
PROJECT_ROOT = NOTEBOOK_DIR.parent.parent  # Go up 2 levels: /.../ufc-fight-predictor/
MODEL_PATH = PROJECT_ROOT / "ml_core" / "models" / "trained_model.joblib"
model = joblib.load(filename=MODEL_PATH)

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

    # Sort by newest fights, then query for their latest fight
    df_fighter = df.sort_values(by="Date", ascending=False)
    df_fighter = df_fighter[(df_fighter["RedFighter"].str.lower() == fighter_name) | (df_fighter["BlueFighter"].str.lower() == fighter_name)].head(1)

    # No fighter history
    if df_fighter.empty:
        raise ValueError(f"No fight history for {fighter_name}")

    if df_fighter["RedFighter"].iloc[0].lower() == fighter_name:
        cols_to_drop = df_fighter.filter(regex='(?i)blue').columns # Columns containing data for opposing fighter
        df_fighter = df_fighter.drop(columns=cols_to_drop) # Keeping only columns pertaining to specified fighter
    else:
        # Same logic, but if queried fighter turned out to be BlueFighter
        cols_to_drop = df_fighter.filter(regex='(?i)red').columns
        df_fighter = df_fighter.drop(columns=cols_to_drop)

    return df_fighter.iloc[0].to_dict()


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