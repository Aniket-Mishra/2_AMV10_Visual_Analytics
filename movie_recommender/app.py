import dash
from dash import dcc, html, callback_context, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
from pathlib import Path
import numpy as np
import random

# --- Configuration & Data Loading ---
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR.parent / "processed_data"
MOVIES_PATH = DATA_DIR / "movies_data_updated.parquet"
RATINGS_PATH = DATA_DIR / "ratings_data_extended.parquet"

DEFAULT_POSTER_URL = "https://placehold.co/300x450/222222/FFFFFF?text=No+Poster"
RATINGS_SAMPLE_SIZE = 200000 # Sample size for ratings data for performance
MIN_VOTES_FOR_INITIAL_DISPLAY = 1000 # For selecting initial movies
MAX_FILTER_RESULTS = 24 # Max movies to show after filtering

# --- Helper Functions ---
def load_data(file_path, is_movies=False, is_ratings=False, sample_size=None):
    """Loads data from parquet file with error handling."""
    try:
        print(f"Loading data from: {file_path}")
        if is_ratings and sample_size:
            df = pd.read_parquet(file_path)
            print(f"Full ratings data loaded, shape: {df.shape}. Sampling to {sample_size} rows.")
            df = df.sample(n=min(sample_size, len(df)), random_state=42)
        else:
            df = pd.read_parquet(file_path)
        
        print(f"Data loaded successfully. Shape: {df.shape}")
        
        if is_movies:
            df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce').astype('Int64')
            df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce').astype('Int64')
            df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce')
            df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').astype('Int64')
            df['poster_url'] = df['poster_url'].astype(str).fillna('')
            df['display_title'] = df['title'] + ' (' + df['release_year'].astype(str).str.replace('<NA>', 'N/A', regex=False) + ')'
            for col in ['director', 'lead_actor', 'main_genre', 'overview', 'tagline']: # Ensure key text fields are strings
                df[col] = df[col].fillna('Unknown').astype(str)
                df[col] = df[col].replace({'<NA>': 'Unknown', 'nan': 'Unknown', '': 'Unknown'})


        if is_ratings:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            df['userId'] = pd.to_numeric(df['userId'], errors='coerce').astype('Int64')
        return df
    except FileNotFoundError:
        print(f"ERROR: Data file not found at {file_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"ERROR: Could not load or process data from {file_path}: {e}")
        return pd.DataFrame()

movies_df = load_data(MOVIES_PATH, is_movies=True)
# ratings_df = load_data(RATINGS_PATH, is_ratings=True, sample_size=RATINGS_SAMPLE_SIZE) # Load if/when needed for recommendations

# --- Prepare Filter Options ---
movie_options_dropdown = []
all_genres = ['Unknown'] # Add Unknown as a default option
all_directors = ['Unknown']
all_lead_actors = ['Unknown']
min_release_year = 1900
max_release_year = pd.Timestamp.now().year # Use current year as max

if not movies_df.empty:
    movie_options_dropdown = [{'label': row['display_title'], 'value': row['movieId']} for _, row in movies_df.sort_values('display_title').iterrows()]
    
    # Get unique values, ensure 'Unknown' is present, and sort
    def get_unique_sorted_values(series, default_value='Unknown'):
        unique_values = series.unique().tolist()
        if default_value not in unique_values:
            unique_values.append(default_value)
        return sorted(list(set(unique_values))) # Use set to ensure unique then sort

    all_genres = get_unique_sorted_values(movies_df['main_genre'])
    all_directors = get_unique_sorted_values(movies_df['director'])
    all_lead_actors = get_unique_sorted_values(movies_df['lead_actor'])
    
    if 'release_year' in movies_df.columns and not movies_df['release_year'].isnull().all():
        min_release_year = int(movies_df['release_year'].min(skipna=True))
        # Ensure max_release_year is not less than min_release_year if data is old
        max_release_year = max(int(movies_df['release_year'].max(skipna=True)), min_release_year)


# --- Initial Movie Showcase Selection ---
def get_initial_showcase_movies(df_movies, num_movies=6):
    if df_movies.empty or len(df_movies) < num_movies:
        return pd.DataFrame()

    # Prioritize movies with posters, more votes and good ratings from diverse top genres
    # Ensure 'poster_url' is not the default placeholder or empty
    valid_poster_movies = df_movies[
        (df_movies['poster_url'].notna()) & \
        (df_movies['poster_url'] != '') & \
        (df_movies['poster_url'] != DEFAULT_POSTER_URL)
    ]
    if valid_poster_movies.empty: # Fallback if no movies have valid posters
        return df_movies.sample(min(num_movies, len(df_movies))) if not df_movies.empty else pd.DataFrame()


    top_genres = valid_poster_movies['main_genre'].value_counts().nlargest(10).index.tolist()
    showcase_movies_list = []
    selected_movie_ids = set()

    for genre in top_genres:
        if len(showcase_movies_list) >= num_movies:
            break
        
        genre_movies = valid_poster_movies[
            (valid_poster_movies['main_genre'] == genre) &
            (valid_poster_movies['vote_count'] >= MIN_VOTES_FOR_INITIAL_DISPLAY) &
            (~valid_poster_movies['movieId'].isin(selected_movie_ids))
        ].sort_values(by=['vote_average', 'vote_count'], ascending=[False, False])
        
        if not genre_movies.empty:
            movie_to_add = genre_movies.iloc[0]
            showcase_movies_list.append(movie_to_add.to_dict())
            selected_movie_ids.add(movie_to_add['movieId'])

    if len(showcase_movies_list) < num_movies:
        additional_movies_needed = num_movies - len(showcase_movies_list)
        other_highly_voted = valid_poster_movies[
            (valid_poster_movies['vote_count'] >= MIN_VOTES_FOR_INITIAL_DISPLAY) &
            (~valid_poster_movies['movieId'].isin(selected_movie_ids))
        ].sort_values(by=['vote_average', 'vote_count'], ascending=[False, False])
        
        showcase_movies_list.extend(other_highly_voted.head(additional_movies_needed).to_dict('records'))

    if not showcase_movies_list: # Fallback if no movies meet criteria
         return valid_poster_movies.sample(min(num_movies, len(valid_poster_movies)))

    return pd.DataFrame(showcase_movies_list)

initial_showcase_df = get_initial_showcase_movies(movies_df, num_movies=6)

# --- App Initialization ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], suppress_callback_exceptions=True)
app.title = "Movie Recommender"

# --- Reusable Components ---
def create_movie_card(movie_data):
    """Creates a Bootstrap card for a movie from a dictionary or Series."""
    poster = movie_data.get('poster_url', DEFAULT_POSTER_URL)
    if not poster or pd.isna(poster) or str(poster).strip() == '':
        poster = DEFAULT_POSTER_URL

    title = str(movie_data.get('title', 'N/A'))
    genre = str(movie_data.get('main_genre', 'N/A'))
    
    raw_vote_avg = movie_data.get('vote_average')
    raw_vote_count = movie_data.get('vote_count')

    vote_avg_display = 'N/A'
    if pd.notna(raw_vote_avg):
        try: vote_avg_display = f"{float(raw_vote_avg):.1f}"
        except (ValueError, TypeError): pass

    vote_count_display = 'N/A'
    if pd.notna(raw_vote_count):
        try: vote_count_display = f"{int(float(raw_vote_count)):,}" # Ensure it's float then int
        except (ValueError, TypeError): pass
            
    rating_text = f"Rating: {vote_avg_display}/10 ({vote_count_display} votes)"
    if vote_avg_display == 'N/A' and vote_count_display == 'N/A': rating_text = "Rating: N/A"
    elif vote_avg_display == 'N/A': rating_text = f"Rating: N/A ({vote_count_display} votes)"
    elif vote_count_display == 'N/A': rating_text = f"Rating: {vote_avg_display}/10"


    return dbc.Card(
        [
            dbc.CardImg(src=poster, top=True, alt=f"Poster for {title}", style={'height': '300px', 'objectFit': 'cover'}),
            dbc.CardBody(
                [
                    html.H5(title, className="card-title", title=title, style={'overflow': 'hidden', 'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap', 'height': '2rem'}),
                    html.P(f"Genre: {genre}", className="card-text", style={'fontSize': '0.9em'}),
                    html.P(rating_text, className="card-text", style={'fontSize': '0.9em'}),
                ]
            )
        ],
        style={"width": "100%", "marginBottom": "15px", "height": "480px"},
        className="shadow bg-secondary" # Slightly lighter card background
    )

# --- App Layout ---
app.layout = dbc.Container(
    fluid=True,
    style={"backgroundColor": "#1a1a1a", "minHeight": "100vh", "color": "#f8f9fa"},
    children=[
        dbc.Row(dbc.Col(html.H1("Movie Recommendation Engine", className="text-center text-primary my-4"), width=12)),
        dbc.Row(
            [
                dbc.Col(dcc.Dropdown(id='genre-filter', options=[{'label': g, 'value': g} for g in all_genres], multi=True, placeholder="Filter by Genre(s)"), width=12, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(id='director-filter', options=[{'label': d, 'value': d} for d in all_directors], placeholder="Filter by Director", clearable=True), width=12, md=3, className="mb-2"),
                dbc.Col(dcc.Dropdown(id='actor-filter', options=[{'label': a, 'value': a} for a in all_lead_actors], placeholder="Filter by Lead Actor", clearable=True), width=12, md=3, className="mb-2"),
                dbc.Col(dbc.Button("Apply Text Filters", id="apply-filters-button", color="primary", className="w-100"), width=12, md=3, className="mb-2")
            ],
            className="mb-4 px-3"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [html.Label("Release Year Range:", className="form-label"),
                     dcc.RangeSlider(id='year-filter', min=min_release_year, max=max_release_year, step=1,
                                     value=[max(min_release_year, max_release_year - 20), max_release_year],
                                     marks={i: str(i) for i in range(min_release_year, max_release_year + 1, 10 if (max_release_year - min_release_year) > 50 else 5)},
                                     tooltip={"placement": "bottom", "always_visible": False})
                    ], width=12, md=6, className="mb-3"
                ),
                dbc.Col(
                    [html.Label("Minimum Average Rating:", className="form-label"),
                     dcc.Slider(id='rating-filter', min=0, max=10, step=0.1, value=6.0,
                                marks={i: str(i) for i in range(0, 11, 1)},
                                tooltip={"placement": "bottom", "always_visible": False})
                    ], width=12, md=6, className="mb-3"
                )
            ],
            className="mb-4 px-3"
        ),
        dbc.Row(dbc.Col(html.H3("Discover Movies", className="text-info mb-3"), width=12), className="px-3"),
        dbc.Spinner(dbc.Row(id='filtered-movies-output', className="px-3 g-3"), color="info"), # g-3 for gutters
        html.Hr(className="my-4"),
        dbc.Row(dbc.Col(html.H4("Or, Select a Specific Movie:", className="text-info mb-3"), width=12), className="px-3"),
        dbc.Row(
            [dbc.Col(dcc.Dropdown(id='movie-dropdown', options=movie_options_dropdown, placeholder="Select a specific movie by title...", className="mb-3"), md=6, className="mx-auto")],
            justify="center", className="px-3"
        ),
        dbc.Row(dbc.Col(dbc.Spinner(html.Div(id='movie-details-output'), color="primary"), width=12, className="mt-2 px-3 pb-5")),
    ]
)

# --- Callbacks ---
@app.callback(
    Output('filtered-movies-output', 'children'),
    [
        Input('apply-filters-button', 'n_clicks'),
        Input('year-filter', 'value'),      # Slider for year range
        Input('rating-filter', 'value')     # Slider for minimum rating
    ],
    [
        State('genre-filter', 'value'),     # Dropdown for genres
        State('director-filter', 'value'),  # Dropdown for director
        State('actor-filter', 'value')      # Dropdown for lead actor
    ]
)
def update_filtered_movies(btn_clicks, selected_years, min_rating, selected_genres, selected_director, selected_actor):
    if not dash.callback_context.triggered: # Initial load
        if not initial_showcase_df.empty:
            filtered_df_display = initial_showcase_df
        elif movies_df.empty:
            return dbc.Alert("Movie data is not available.", color="danger", className="mt-3 text-center")
        else: # No showcase, but movies_df exists
            return dbc.Alert("No initial movies to display. Use filters to find movies or select from dropdown.", color="info", className="mt-3 text-center")
    
    elif movies_df.empty:
        return dbc.Alert("Movie data is not available to filter.", color="warning", className="mt-3 text-center")
    else:
        # Apply all filters when any relevant input changes
        filtered_df = movies_df.copy()

        if selected_genres:
            filtered_df = filtered_df[filtered_df['main_genre'].isin(selected_genres)]
        if selected_director and selected_director != 'Unknown': # Handle 'Unknown' if it's a placeholder
            filtered_df = filtered_df[filtered_df['director'] == selected_director]
        if selected_actor and selected_actor != 'Unknown':
            filtered_df = filtered_df[filtered_df['lead_actor'] == selected_actor]
        
        if selected_years:
            filtered_df = filtered_df[
                (filtered_df['release_year'] >= selected_years[0]) &
                (filtered_df['release_year'] <= selected_years[1])
            ]
        if min_rating is not None: 
            filtered_df = filtered_df[filtered_df['vote_average'] >= min_rating]
        
        filtered_df_display = filtered_df.sort_values(
            by=['vote_count', 'vote_average'], ascending=[False, False]
        ).head(MAX_FILTER_RESULTS)

    if filtered_df_display.empty:
        return dbc.Alert("No movies match your criteria.", color="info", className="mt-3 text-center")

    movie_cards = [
        dbc.Col(create_movie_card(movie_row), width=12, sm=6, md=4, lg=3, className="mb-4 d-flex align-items-stretch") # align-items-stretch for equal height cards
        for _, movie_row in filtered_df_display.iterrows()
    ]
    return movie_cards


@app.callback(
    Output('movie-details-output', 'children'),
    [Input('movie-dropdown', 'value')]
)
def display_selected_movie_details(selected_movie_id):
    if not selected_movie_id:
        return dbc.Alert("Select a specific movie from the dropdown above to see its details.", color="secondary", className="mt-3 text-center")

    if movies_df.empty:
        return dbc.Alert("Movie data is not available.", color="danger", className="mt-3 text-center")

    # Ensure selected_movie_id is of the correct type for comparison if movies_df['movieId'] is not int
    try:
        selected_movie_id = int(selected_movie_id) 
    except ValueError:
        return dbc.Alert("Invalid movie selection.", color="danger", className="mt-3 text-center")


    movie_info_series = movies_df[movies_df['movieId'] == selected_movie_id]
    if movie_info_series.empty:
        return dbc.Alert(f"Movie with ID {selected_movie_id} not found.", color="warning", className="mt-3 text-center")
    
    movie_info = movie_info_series.iloc[0] # Now a Series

    poster_url = movie_info.get('poster_url', DEFAULT_POSTER_URL)
    if not poster_url or pd.isna(poster_url) or str(poster_url).strip() == '':
        poster_url = DEFAULT_POSTER_URL
    
    title = str(movie_info.get('title', 'N/A'))
    overview = str(movie_info.get('overview', 'N/A'))
    tagline = str(movie_info.get('tagline', ''))
    main_genre_val = str(movie_info.get('main_genre', 'N/A'))
    release_year_val = str(movie_info.get('release_year', 'N/A'))
    director_val = str(movie_info.get('director', 'N/A'))
    lead_actor_val = str(movie_info.get('lead_actor', 'N/A'))
    
    raw_runtime = movie_info.get('runtime')
    raw_vote_avg = movie_info.get('vote_average')
    raw_vote_count = movie_info.get('vote_count')

    runtime_display = 'N/A'
    if pd.notna(raw_runtime):
        try: runtime_display = f"{int(float(raw_runtime))} min"
        except (ValueError, TypeError): pass
        
    vote_avg_display = 'N/A'
    if pd.notna(raw_vote_avg):
        try: vote_avg_display = f"{float(raw_vote_avg):.1f}/10"
        except (ValueError, TypeError): pass

    vote_count_display = 'N/A'
    if pd.notna(raw_vote_count):
        try: vote_count_display = f"{int(float(raw_vote_count)):,}"
        except (ValueError, TypeError): pass
    
    final_rating_display = f"{vote_avg_display} (from {vote_count_display} votes)"
    if vote_avg_display == 'N/A' and vote_count_display == 'N/A': final_rating_display = "N/A"
    elif vote_avg_display == 'N/A': final_rating_display = f"N/A (from {vote_count_display} votes)"
    elif vote_count_display == 'N/A': final_rating_display = f"{vote_avg_display}"


    details_layout = dbc.Card(
        dbc.Row(
            [
                dbc.Col(html.Img(src=poster_url, className="img-fluid rounded", style={'maxHeight': '450px', 'objectFit': 'cover'}), md=4, className="d-flex justify-content-center align-items-start p-3"),
                dbc.Col(
                    [
                        html.H3(title, className="card-title"),
                        html.H5(tagline, className="card-subtitle mb-2 text-muted") if tagline and tagline.lower() not in ['unknown', 'n/a'] else "",
                        html.Hr(),
                        dbc.Row([dbc.Col(html.Strong("Release Year:"), width="auto", className="pe-0"), dbc.Col(release_year_val)]),
                        dbc.Row([dbc.Col(html.Strong("Runtime:"), width="auto", className="pe-0"), dbc.Col(runtime_display)]),
                        dbc.Row([dbc.Col(html.Strong("Main Genre:"), width="auto", className="pe-0"), dbc.Col(main_genre_val)]),
                        dbc.Row([dbc.Col(html.Strong("Director:"), width="auto", className="pe-0"), dbc.Col(director_val)]),
                        dbc.Row([dbc.Col(html.Strong("Lead Actor:"), width="auto", className="pe-0"), dbc.Col(lead_actor_val)]),
                        html.Hr(),
                        html.Strong("Overview:"),
                        html.P(overview if overview.lower() not in ['unknown', 'n/a'] else "No overview available.", className="card-text mt-2"),
                        html.Hr(),
                        dbc.Row([dbc.Col(html.Strong("Avg. Rating:"), width="auto", className="pe-0"), dbc.Col(final_rating_display)]),
                    ], md=8, className="p-3"
                ),
            ], className="g-0" # No gutters for closer alignment
        ), className="mt-3 shadow bg-dark"
    )
    return details_layout

# --- Run the App ---
if __name__ == '__main__':
    print("Attempting to run the Dash server...")
    app.run_server(debug=True, port=8051) 
    print("Dash server should be running.")

