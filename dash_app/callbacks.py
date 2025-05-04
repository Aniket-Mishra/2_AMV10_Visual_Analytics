# callbacks.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output # Import State here if needed
import numpy as np # For np.stack

# --- Helper Function for Filtering ---
def filter_data(df, selected_genres, selected_years, min_vote_count):
    """
    Applies filters based on user selections.

    Args:
        df (pd.DataFrame): The original DataFrame.
        selected_genres (list or None): List of selected genres from dropdown.
        selected_years (list or None): [min_year, max_year] from slider.
        min_vote_count (int or None): Minimum vote count from slider.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    filtered_df = df.copy()

    # Filter by selected genres
    if selected_genres and len(selected_genres) > 0:
        if 'main_genre' in filtered_df.columns:
             filtered_df = filtered_df[filtered_df['main_genre'].isin(selected_genres)]

    # Filter by release year range
    if selected_years and len(selected_years) == 2:
        if 'release_year' in filtered_df.columns:
            min_year, max_year = selected_years
            # Ensure year column is numeric before comparison - done in data_prep, but defensive here
            # filtered_df['release_year'] = pd.to_numeric(filtered_df['release_year'], errors='coerce').dropna() # Dropping NaN in filter helper might be too aggressive
            filtered_df = filtered_df[(filtered_df['release_year'] >= min_year) & (filtered_df['release_year'] <= max_year)]


    # Filter by minimum vote count
    if min_vote_count is not None:
         if 'vote_count' in filtered_df.columns:
            # Ensure vote_count is numeric before comparison - done in data_prep, but defensive here
            # filtered_df['vote_count'] = pd.to_numeric(filtered_df['vote_count'], errors='coerce').fillna(0)
            filtered_df = filtered_df[filtered_df['vote_count'] >= min_vote_count]

    return filtered_df

# --- Helper Functions for Generating Specific Graphs ---

def create_year_count_graph(filtered_df):
    """Creates the Movies per Year bar chart."""
    fig = go.Figure()
    if 'release_year' in filtered_df.columns and not filtered_df['release_year'].isnull().all() and not filtered_df.empty:
         # Ensure release_year is numeric, drop NaNs just for this plot aggregation if any slipped through
         year_data = filtered_df.dropna(subset=['release_year'])
         if not year_data.empty:
            movies_per_year = year_data['release_year'].value_counts().sort_index().reset_index()
            movies_per_year.columns = ['Year', 'Count']
            fig = px.bar(movies_per_year, x='Year', y='Count',
                         title='Number of Movies Released Per Year')
         else:
              fig.update_layout(title="Movies per Year: No data matching filters.")

    else:
        fig.update_layout(title="Movies per Year: Data not suitable.")
    return fig

def create_budget_revenue_scatter(filtered_df):
    """Creates the Budget vs Revenue scatter plot."""
    fig = go.Figure()
    required_cols = ['budget', 'revenue', 'title', 'main_genre', 'vote_count']
    if all(col in filtered_df.columns for col in required_cols):
        # Filter out movies with 0 budget and 0 revenue for a cleaner scatter plot
        scatter_df = filtered_df[(filtered_df['budget'] > 0) | (filtered_df['revenue'] > 0)].copy()
        if not scatter_df.empty:
            # Ensure numeric columns are numeric
            scatter_df['budget'] = pd.to_numeric(scatter_df['budget'], errors='coerce')
            scatter_df['revenue'] = pd.to_numeric(scatter_df['revenue'], errors='coerce')
            scatter_df['vote_count'] = pd.to_numeric(scatter_df['vote_count'], errors='coerce')
            # Drop NaNs from plotting columns if px can't handle them gracefully
            scatter_df.dropna(subset=['budget', 'revenue', 'vote_count', 'main_genre', 'title'], inplace=True)


            if not scatter_df.empty:
                 fig = px.scatter(scatter_df,
                                 x='budget',
                                 y='revenue',
                                 hover_name='title',
                                 color='main_genre',
                                 size='vote_count',
                                 log_x=True,
                                 log_y=True,
                                 title='Budget vs. Revenue (Log Scale)')
                 fig.update_layout(xaxis_title='Budget', yaxis_title='Revenue')
                 # Update hover template
                 fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>Budget: %{x:$,.2f}<br>Revenue: %{y:$,.2f}<br>Genre: %{customdata[0]}<br>Votes: %{marker.size}<extra></extra>",
                                   customdata=np.stack((scatter_df.get('main_genre', [None]*len(scatter_df)),), axis=-1))
            else:
                 fig.update_layout(title="Budget vs. Revenue: No data after cleaning.")
        else:
             fig.update_layout(title="Budget vs. Revenue: No movies with budget/revenue > 0.")
    else:
        fig.update_layout(title="Budget vs. Revenue: Required columns missing.")

    return fig

def create_rating_genre_box(filtered_df):
    """Creates the Vote Average by Genre box plot."""
    fig = go.Figure()
    required_cols = ['main_genre', 'vote_average']
    if all(col in filtered_df.columns for col in required_cols):
        # Consider only genres with a minimum number of movies to avoid noisy boxes
        # Drop rows with NaN main_genre before counting
        genre_counts_df = filtered_df.dropna(subset=['main_genre']).copy()
        genre_counts = genre_counts_df['main_genre'].value_counts()
        # Only include genres that have at least 10 movies AND are not 'Unknown'
        genres_to_plot = genre_counts[(genre_counts >= 10) & (genre_counts.index != 'Unknown')].index.tolist()

        rating_genre_df = filtered_df[filtered_df['main_genre'].isin(genres_to_plot)].copy()
        # Ensure vote_average is numeric and drop NaNs for plotting
        if 'vote_average' in rating_genre_df.columns:
             rating_genre_df['vote_average'] = pd.to_numeric(rating_genre_df['vote_average'], errors='coerce')
             rating_genre_df.dropna(subset=['vote_average', 'main_genre'], inplace=True)


        if not rating_genre_df.empty:
             fig = px.box(rating_genre_df, x='main_genre', y='vote_average',
                          title='Vote Average Distribution by Main Genre (Genres with >= 10 movies)')
             fig.update_layout(xaxis_title='Main Genre', yaxis_title='Vote Average')
        else:
            fig.update_layout(title="Rating by Genre: No data matching criteria.")
    else:
         fig.update_layout(title="Rating by Genre: Required columns missing.")

    return fig


# --- Function to Register Callbacks ---
def register_callbacks(app, df):
    """
    Registers all callbacks with the Dash app instance.

    Args:
        app (dash.Dash): The Dash app instance.
        df (pd.DataFrame): The main DataFrame.
    """

    @app.callback(
        [Output('movies-per-year-graph', 'figure'),
         Output('budget-revenue-scatter', 'figure'),
         Output('rating-by-genre-box', 'figure')],
        [Input('genre-dropdown', 'value'),
         Input('year-slider', 'value'),
         Input('vote-count-slider', 'value')]
    )
    def update_graphs(selected_genres, selected_years, min_vote_count):
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

        # --- Apply Filters using helper function ---
        filtered_df = filter_data(df, selected_genres, selected_years, min_vote_count)

        print(f"Filtered DataFrame shape: {filtered_df.shape}")

        # Handle case where filtering results in an empty DataFrame
        if filtered_df.empty:
            print("Filtered DataFrame is empty, returning empty figures with message.")
            empty_fig = go.Figure()
            empty_fig.update_layout(title="No data matches the filters.",
                                    xaxis={'visible': False}, yaxis={'visible': False},
                                    annotations=[{'text': 'Adjust filter settings',
                                                  'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 20}}])
            # Return empty figures for all outputs
            return empty_fig, empty_fig, empty_fig

        print(f"Filtered DataFrame is NOT empty. Shape: {filtered_df.shape}")

        # --- Generate Figures using helper functions ---
        # Each function handles its own potential data suitability issues and returns a figure
        fig_year_count = create_year_count_graph(filtered_df)
        fig_budget_revenue = create_budget_revenue_scatter(filtered_df)
        fig_rating_genre = create_rating_genre_box(filtered_df)

        print("--- Callback Finished ---")
        return fig_year_count, fig_budget_revenue, fig_rating_genre

    # --- Add more callbacks here for interactivity like brushing/linking ---
    # @app.callback(...)
    # def update_details(selected_data_from_graph):
    #     # Logic to show details of selected movies
    #     pass

    # @app.callback(...)
    # def highlight_on_brush(selected_data_from_graph, current_figures_state):
    #     # Logic to modify other figures based on selection
    #     pass