# data_prep.py
import pandas as pd
import numpy as np
import ast # Assuming ast is still needed from your original processing
import traceback

def load_and_prepare_data(data_path):
    """
    Loads the movie data from a parquet file and performs necessary cleaning
    and preparation for use in the Dash app.

    Args:
        data_path (str): The path to the parquet file.

    Returns:
        tuple: A tuple containing:
            - df (pd.DataFrame): The cleaned DataFrame.
            - available_genres (list): Sorted list of unique main genres.
            - available_release_years (list): Sorted list of unique release years.
            - max_vote_count (int): Maximum vote count for the slider.
            - max_budget (int): Maximum budget for potential slider/marks.
            - max_revenue (int): Maximum revenue for potential slider/marks.
    """
    df = pd.DataFrame() # Initialize empty df
    available_genres = []
    available_release_years = []
    max_vote_count = 1000
    max_budget = 0
    max_revenue = 0

    try:
        df = pd.read_parquet(data_path)
        print("Data loaded successfully.")
        print(f"Initial DataFrame shape: {df.shape}")

        # --- Data Preparation/Cleaning for Plotting ---
        if not df.empty:
            print("Starting data preparation for plotting...")

            # Ensure numeric columns are numeric and handle NaNs
            numeric_cols_fillna_0 = ['vote_count', 'budget', 'revenue', 'runtime', 'popularity_score']
            numeric_cols_no_fillna = ['release_year', 'vote_average']

            for col in numeric_cols_fillna_0 + numeric_cols_no_fillna:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Fill NaNs where appropriate (e.g., counts, financials)
            for col in numeric_cols_fillna_0:
                 if col in df.columns:
                      df[col] = df[col].fillna(0)

            # Handle NaNs for release_year specifically
            if 'release_year' in df.columns:
                initial_rows = df.shape[0]
                df.dropna(subset=['release_year'], inplace=True)
                if df.shape[0] < initial_rows:
                    print(f"Dropped {initial_rows - df.shape[0]} rows with missing release_year.")
                df['release_year'] = df['release_year'].astype(int)

            # Fill NaN for categorical features
            categorical_cols = ['main_genre', 'director', 'main_production_company', 'main_country',
                                'main_language', 'runtime_bin', 'collection_name', 'producer',
                                'lead_actor', 'other_lead', 'title']
            for col in categorical_cols:
                if col in df.columns:
                     df[col] = df[col].astype('object')
                     df[col] = df[col].fillna('Unknown')

            # --- Extract values for controls and stats ---
            if 'main_genre' in df.columns:
                 available_genres = sorted(df['main_genre'].unique().tolist())
                 # Optional: remove 'Unknown' from initial dropdown options if desired, add back later
                 # if 'Unknown' in available_genres: available_genres.remove('Unknown')

            if 'release_year' in df.columns:
                 available_release_years = sorted(df['release_year'].unique().tolist())

            if 'vote_count' in df.columns and not df.empty:
                 max_vote_count = int(df['vote_count'].max())

            if 'budget' in df.columns and not df.empty:
                 max_budget = int(df['budget'].max())

            if 'revenue' in df.columns and not df.empty:
                 max_revenue = int(df['revenue'].max())


            print("Data preparation complete.")
            print(f"DataFrame shape after preparation: {df.shape}")
        else:
            print("DataFrame is empty after loading.")


    except FileNotFoundError:
        print(f"Error: Data file not found at {data_path}")
    except Exception as e:
        print(f"An error occurred while loading data: {e}")
        print(traceback.format_exc())

    return df, available_genres, available_release_years, max_vote_count, max_budget, max_revenue

# Example usage (if you want to test this module separately)
if __name__ == '__main__':
    test_path = "/Users/aniket/TU_Eindhoven/2_Study/Q4_2AMV10_Visual_Analytics/4_Code/2_AMV10_Visual_Analytics/processed_data/movies_data_updated.parquet"
    test_df, genres, years, max_votes, _, _ = load_and_prepare_data(test_path)
    print("\n--- Test Results ---")
    print(f"Loaded DataFrame shape: {test_df.shape}")
    print(f"Sample genres: {genres[:10]}")
    print(f"Sample years: {years[:10]}")
    print(f"Max vote count: {max_votes}")
    # print(test_df.head())