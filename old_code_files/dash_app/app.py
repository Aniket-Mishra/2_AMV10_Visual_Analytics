# app.py
import dash
import data_prep
import layout
import callbacks
import os # Import os for joining path

# --- Configuration ---
data_file_path = "/Users/aniket/TU_Eindhoven/2_Study/Q4_2AMV10_Visual_Analytics/4_Code/2_AMV10_Visual_Analytics/processed_data/movies_data_updated.parquet"

# --- Load and Prepare Data ---
# This is done once when the app starts
df, available_genres, available_release_years, max_vote_count, _, _ = data_prep.load_and_prepare_data(data_file_path)

# --- Initialize the Dash App ---
app = dash.Dash(__name__)
# Optional: set app.title
app.title = "Movie Data Analytics"

# --- Define App Layout ---
# The layout is created using the function from layout.py
app.layout = layout.create_layout(available_genres, available_release_years, max_vote_count)

# --- Register Callbacks ---
# All callback logic is registered here
callbacks.register_callbacks(app, df)

# --- Run the App ---
if __name__ == '__main__':
    # Use debug=True during development for hot-reloading and error messages
    # Set debug=False for production deployment
    app.run_server(debug=True)