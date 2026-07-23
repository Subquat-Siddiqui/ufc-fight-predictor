"""
This file will contain necessary logic for when a user tries to predict a matchup between 2 fighters.
The logic includes retrieving the latest fighter stats, retrieving live betting odds, and then predicting the winner.
"""
from pathlib import Path
import pandas as pd
import joblib
import requests

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