import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State # Import State if needed later
from collections import Counter
import traceback # To print detailed error in callback


# --- Load your processed data ---
# Make sure the path is correct for your environment
data_path = "/Users/aniket/TU_Eindhoven/2_Study/Q4_2AMV10_Visual_Analytics/4_Code/2_AMV10_Visual_Analytics/processed_data/movies_data_updated.parquet"
df = pd.DataFrame() # Initialize empty df in case of loading errors
try:
    df = pd.read_parquet(data_path)
    print("Data loaded successfully.")
    print(f"Initial DataFrame shape: {df.shape}")
    # print("Columns:", df.columns.tolist()) # Uncomment if you want to see columns again

except FileNotFoundError:
    print(f"Error: Data file not found at {data_path}")
except Exception as e:
    print(f"An error occurred while loading data: {e}")
    print(traceback.format_exc()) # Print full traceback for loading error


# --- Data Preparation/Cleaning for Plotting ---
if not df.empty:
    print("Starting data preparation for plotting...")

    # Ensure numeric columns are numeric and handle NaNs
    numeric_cols_fillna_0 = ['vote_count', 'budget', 'revenue', 'runtime', 'popularity_score']
    numeric_cols_no_fillna = ['release_year', 'vote_average'] # vote_average might be better left as NaN or dropped if unknown

    for col in numeric_cols_fillna_0 + numeric_cols_no_fillna:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill NaNs where appropriate (e.g., counts, financials)
    for col in numeric_cols_fillna_0:
         if col in df.columns:
              df[col] = df[col].fillna(0)

    # Handle NaNs for release_year specifically if needed.
    # For time-based plots, rows without a release year are problematic.
    # Option 1: Drop rows with NaN release_year
    if 'release_year' in df.columns:
        initial_rows = df.shape[0]
        df.dropna(subset=['release_year'], inplace=True)
        if df.shape[0] < initial_rows:
            print(f"Dropped {initial_rows - df.shape[0]} rows with missing release_year.")
        df['release_year'] = df['release_year'].astype(int) # Convert to int after dropping NaNs

    # Fill NaN for categorical features that might be used in filters/plots
    # Convert to object dtype first to avoid Categorical dtype issues with new categories
    categorical_cols = ['main_genre', 'director', 'main_production_company', 'main_country',
                        'main_language', 'runtime_bin', 'collection_name', 'producer',
                        'lead_actor', 'other_lead', 'title'] # Added title as well
    for col in categorical_cols:
        if col in df.columns:
             # Convert to object dtype before filling NaNs with a potentially new string
             df[col] = df[col].astype('object')
             df[col] = df[col].fillna('Unknown')

    # Extract unique values for dropdowns (handle potential NaNs if not filled above)
    available_genres = sorted(df['main_genre'].unique().tolist()) if 'main_genre' in df.columns and not df['main_genre'].isnull().all() else []
    # Keep 'Unknown' in the options if it was added during fillna
    # If you want 'Unknown' first: available_genres = ['Unknown'] + [g for g in available_genres if g != 'Unknown']


    available_release_years = sorted(df['release_year'].dropna().astype(int).unique().tolist()) if 'release_year' in df.columns and not df['release_year'].isnull().all() else []

    print("Data preparation complete.")
    print(f"DataFrame shape after preparation: {df.shape}")
else:
    print("Skipping data preparation as DataFrame is empty.")


# --- Initialize the Dash App ---
app = dash.Dash(__name__)

# --- Define App Layout ---
app.layout = html.Div([
    html.H1("Movie Data Visual Analytics"),

    # --- Control Panel ---
    html.Div([
        html.Div([
            html.Label("Select Main Genre:"),
            dcc.Dropdown(
                id='genre-dropdown',
                options=[{'label': genre, 'value': genre} for genre in available_genres], # Include 'Unknown' if present
                value=None, # No default selection
                multi=True # Allow selecting multiple genres
            )
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Select Release Year Range:"),
            dcc.RangeSlider(
                id='year-slider',
                min=min(available_release_years) if available_release_years else 1900,
                max=max(available_release_years) if available_release_years else 2025,
                value=[min(available_release_years) if available_release_years else 1900, max(available_release_years) if available_release_years else 2025],
                marks={year: str(year) for year in range(min(available_release_years) if available_release_years else 1900, max(available_release_years) if available_release_years else 2025, max(1, int((max(available_release_years) - min(available_release_years)) / 10)) )}, # Dynamic marks
                step=1,
                 allowCross=False # Prevent start > end
            )
        ], style={'width': '48%', 'display': 'inline-block', 'paddingLeft': '2%'}),

         html.Div([
            html.Label("Minimum Vote Count:"),
            dcc.Slider(
                id='vote-count-slider',
                min=0,
                max=df['vote_count'].max() if 'vote_count' in df.columns and not df.empty else 1000,
                value=10, # Default minimum votes to consider
                marks={0: '0', 100: '100', 500: '500', 1000: '1k', 5000: '5k', 10000: '10k'} if ('vote_count' in df.columns and not df.empty and df['vote_count'].max() > 5000) else {0: '0', 100: '100', 500: '500', 1000: '1k'},
                step=max(1, int( (df['vote_count'].max() if 'vote_count' in df.columns and not df.empty else 1000) / 50)), # Dynamic step
                tooltip={"placement": "bottom", "always_visible": True}, # Show current value
            )
        ], style={'width': '98%', 'paddingTop': '20px'}),

    ], style={'padding': '20px', 'border': '1px solid #d3d3d3', 'marginBottom': '20px'}),

    # --- Visualizations Area ---
    html.Div([
        dcc.Graph(id='movies-per-year-graph', style={'height': '400px'}), # Added height
        dcc.Graph(id='budget-revenue-scatter', style={'height': '400px'}), # Added height
        dcc.Graph(id='rating-by-genre-box', style={'height': '400px'}),    # Added height
        # Add more graphs here
    ])
])


# Callback to update graphs based on filter selections
@app.callback(
    [Output('movies-per-year-graph', 'figure'),
     Output('budget-revenue-scatter', 'figure'),
     Output('rating-by-genre-box', 'figure')],
    [Input('genre-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('vote-count-slider', 'value')]
)
def update_graphs(selected_genres, selected_years, min_vote_count):
    # --- Add Print Statements for Debugging ---
    print("\n--- Callback Triggered ---")
    print(f"Selected Genres: {selected_genres}")
    print(f"Selected Years: {selected_years}")
    print(f"Minimum Vote Count: {min_vote_count}")
    print(f"Initial df shape in callback: {df.shape}")


    if df.empty:
        print("df is empty, returning empty figures.")
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Data not loaded.")
        return empty_fig, empty_fig, empty_fig

    # --- Apply Filters ---
    filtered_df = df.copy()
    print(f"Shape after initial copy: {filtered_df.shape}")

    # Filter by selected genres
    if selected_genres and len(selected_genres) > 0:
        # Ensure column exists and filter
        if 'main_genre' in filtered_df.columns:
             filtered_df = filtered_df[filtered_df['main_genre'].isin(selected_genres)]
             print(f"Shape after genre filter: {filtered_df.shape}")
        else:
            print("Warning: 'main_genre' column not found for filtering.")


    # Filter by release year range
    if selected_years and len(selected_years) == 2:
        # Ensure column exists and filter
        if 'release_year' in filtered_df.columns:
            min_year, max_year = selected_years
            # Ensure year column is numeric before comparison
            filtered_df['release_year'] = pd.to_numeric(filtered_df['release_year'], errors='coerce')
            # Drop rows where release_year became NaN after coercion just for filtering step
            filtered_df = filtered_df.dropna(subset=['release_year'])
            filtered_df = filtered_df[(filtered_df['release_year'] >= min_year) & (filtered_df['release_year'] <= max_year)]
            print(f"Shape after year filter: {filtered_df.shape}")
        else:
             print("Warning: 'release_year' column not found for filtering.")


    # Filter by minimum vote count
    if min_vote_count is not None:
         # Ensure column exists and is numeric before comparison
         if 'vote_count' in filtered_df.columns:
            filtered_df['vote_count'] = pd.to_numeric(filtered_df['vote_count'], errors='coerce').fillna(0) # Fill NaN with 0 again just in case
            filtered_df = filtered_df[filtered_df['vote_count'] >= min_vote_count]
            print(f"Shape after vote count filter: {filtered_df.shape}")
         else:
             print("Warning: 'vote_count' column not found for filtering.")


    # Handle case where filtering results in an empty DataFrame
    if filtered_df.empty:
        print("Filtered DataFrame is empty, returning empty figures.")
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No data matches the filters.",
                                xaxis={'visible': False}, yaxis={'visible': False},
                                annotations=[{'text': 'Adjust filter settings',
                                              'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 20}}])
        return empty_fig, empty_fig, empty_fig

    print(f"Filtered DataFrame is NOT empty. Shape: {filtered_df.shape}")
    # print(f"Filtered df columns: {filtered_df.columns.tolist()}") # Uncomment for more detailed debug
    # print(f"Filtered df info:\n{filtered_df.info()}") # Uncomment for more detailed debug


    # --- Generate Figures ---
    fig_year_count = go.Figure() # Initialize figures
    fig_budget_revenue = go.Figure()
    fig_rating_genre = go.Figure()

    # Figure 1: Movies per Year (Bar Chart)
    # Ensure 'release_year' is numeric and handle potential NaNs that might remain
    if 'release_year' in filtered_df.columns and not filtered_df['release_year'].isnull().all():
            movies_per_year = filtered_df['release_year'].value_counts().sort_index().reset_index()
            movies_per_year.columns = ['Year', 'Count']
            fig_year_count = px.bar(movies_per_year, x='Year', y='Count',
                                    title='Number of Movies Released Per Year')
    else:
        print("Skipping Movies per Year graph: 'release_year' data not suitable.")
        fig_year_count.update_layout(title="Movies per Year: Data not available") # Update empty fig title


    # Figure 2: Budget vs. Revenue (Scatter Plot)
    # Filter out movies with 0 budget and 0 revenue for a cleaner scatter plot
    if all(col in filtered_df.columns for col in ['budget', 'revenue', 'title', 'main_genre', 'vote_count']):
        scatter_df = filtered_df[(filtered_df['budget'] > 0) | (filtered_df['revenue'] > 0)].copy()
        if not scatter_df.empty:
            fig_budget_revenue = px.scatter(scatter_df,
                                            x='budget',
                                            y='revenue',
                                            hover_name='title', # Use 'title' now
                                            color='main_genre',
                                            size='vote_count',
                                            log_x=True,
                                            log_y=True,
                                            title='Budget vs. Revenue (Log Scale)')
            fig_budget_revenue.update_layout(xaxis_title='Budget', yaxis_title='Revenue')
                # Update hover template to match new column names and structure
            fig_budget_revenue.update_traces(hovertemplate="<b>%{hovertext}</b><br>Budget: %{x:$,.2f}<br>Revenue: %{y:$,.2f}<br>Genre: %{customdata[0]}<br>Votes: %{marker.size}<extra></extra>",
                                                customdata=np.stack((scatter_df.get('main_genre', [None]*len(scatter_df)),), axis=-1)) # Use .get with default for safety
        else:
                print("Skipping Budget vs Revenue scatter: No movies with budget/revenue > 0 after filters.")
                fig_budget_revenue.update_layout(title="Budget vs. Revenue: No data")
    else:
            print("Skipping Budget vs Revenue scatter: Required columns missing.")
            fig_budget_revenue.update_layout(title="Budget vs. Revenue: Data not available")


    # Figure 3: Rating Distribution by Genre (Box Plot)
    if all(col in filtered_df.columns for col in ['main_genre', 'vote_average']):
        # Consider only genres with a minimum number of movies to avoid noisy boxes
        genre_counts = filtered_df['main_genre'].value_counts()
        # Only include genres that have at least 10 movies AND are not 'Unknown' (optional, depending on if you want to plot 'Unknown')
        genres_to_plot = genre_counts[(genre_counts >= 10) & (genre_counts.index != 'Unknown')].index.tolist()

        rating_genre_df = filtered_df[filtered_df['main_genre'].isin(genres_to_plot)].copy()
        # Ensure vote_average is numeric and drop NaNs for plotting
        if 'vote_average' in rating_genre_df.columns:
                rating_genre_df.dropna(subset=['vote_average'], inplace=True)

        if not rating_genre_df.empty:
                fig_rating_genre = px.box(rating_genre_df, x='main_genre', y='vote_average',
                                        title='Vote Average Distribution by Main Genre (Genres with >= 10 movies)')
                fig_rating_genre.update_layout(xaxis_title='Main Genre', yaxis_title='Vote Average')
        else:
            print("Skipping Rating by Genre box plot: No data for genres with >= 10 movies or no valid ratings.")
            fig_rating_genre.update_layout(title="Rating by Genre: No data")
    else:
        print("Skipping Rating by Genre box plot: Required columns missing.")
        fig_rating_genre.update_layout(title="Rating by Genre: Data not available")

    # Return the generated figures
    print("--- Callback Finished Successfully ---")
    return fig_year_count, fig_budget_revenue, fig_rating_genre

# --- Run the App ---
if __name__ == '__main__':
    # Use debug=True during development
    app.run_server(debug=True)