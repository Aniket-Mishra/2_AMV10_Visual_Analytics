import dash
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
from common_functions import * 
import json

# get data
df_movies = pd.read_parquet("data/1_movies_data_for_app.parquet")
df_users = pd.read_parquet("data/all_users_stats_with_clusters.parquet")
df_ratings = pd.read_parquet("data/processed_df_ratings_filtered.parquet")

# and topic data
with open('data/topic_words.json', 'r') as f:
    topic_dicts = json.load(f)
    topic_words = topic_dicts['overview_topic_words']
    topic_words = {int(k): v for k, v in topic_words.items()}
    tag_topic_words = topic_dicts['tag_topic_words']
    tag_topic_words = {int(k): v for k, v in tag_topic_words.items()}
    keywords_topic_words = topic_dicts['keywords_topic_words']
    keywords_topic_words = {int(k): v for k, v in keywords_topic_words.items()}

# get min and max year for slider
year_min_max = get_column_min_max(df_movies, 'release_year')
year_min = year_min_max['min_value']
year_max = year_min_max['max_value']

# get max vote count for slider
vote_count_min_max = get_column_min_max(df_movies, 'vote_count')
vote_count_max = vote_count_min_max['max_value']

# get list of directors
directors = get_column_unique_values(df_movies, 'director')
director2id = {director: idx for idx, director in enumerate(sorted(directors))}
id2director = {idx: director for director, idx in director2id.items()}

# get list of lead actors
lead_actors = get_column_unique_values(df_movies, 'lead_actor')
actor2id = {actor: idx for idx, actor in enumerate(sorted(lead_actors))}
id2actor = {idx: actor for actor, idx in actor2id.items()}

# get list of genres
main_genres = get_column_unique_values(df_movies, 'main_genre')
all_genres_from_list = set(g for genres in df_movies['genre_list'] for g in genres)
all_genres_from_main = set(main_genres)
all_genres = all_genres_from_list | all_genres_from_main
genre2id = {genre: idx for idx, genre in enumerate(sorted(all_genres))}
id2genre = {idx: genre for genre, idx in genre2id.items()}

# get list of original langueges
original_languages = get_column_unique_values(df_movies, 'original_language')

overview_topic_cols, tag_topic_cols, keywords_topic_cols, core_num_columns = get_core_num_columns(df_movies)


# actual app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "MovieLens: MRAR"

# layout page 1 (movie analysis)
app.layout = html.Div([
    
    
    # navbar (for user and going to second page)
    dbc.NavbarSimple(
        children=[
            dcc.Dropdown(
                id='user_dropdown',
                options=[{'label': f'User {i}', 'value': f'user_{i}'} for i in range(1, 5)],
                value='user_4',
                style={'width': '150px'}
            )
        ],
        brand="MovieLens: Movie Rating Analysis and Recommendation",
        color="primary",
        dark=True,
        className="mb-4"
    ),

    dbc.Container([

        dbc.Row([

            # sidebar filter
            dbc.Col([
                html.H5("Filters", className="mb-3"),

                html.Label("Directors"),
                dcc.Dropdown(
                    id='director_dropdown',
                    options=[{'label': director, 'value': director} for director in directors],
                    value=None, multi=True,
                    placeholder="Select a director...",
                ),
                html.Br(),

                html.Label("Lead Actors"),
                dcc.Dropdown(
                    id='actor_dropdown',
                    options=[{'label': actor, 'value': actor} for actor in lead_actors],
                    value=None, multi=True,
                    placeholder="Select a lead actor...",
                ),
                html.Br(),

                html.Label("Main Genres"),
                dcc.Dropdown(
                    id='genre_dropdown',
                    options=[{'label': genre, 'value': genre} for genre in main_genres],
                    value=None, multi=True,
                    placeholder="Select a main genre...",
                ),
                html.Br(),

                html.Label("Original Language"),
                dcc.Dropdown(
                    id='language_dropdown',
                    options=[{'label': language, 'value': language} for language in original_languages],
                    value=None, multi=True,
                    placeholder="Select an original language...",
                ),
                html.Br(),

                html.Label("Movie Release Year"),
                dcc.RangeSlider(
                    id='release_year_slider',
                    min=year_min, max=year_max, step=1, value=[year_min, year_max],
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Br(),

                html.Label("Movie Rating"),
                dcc.RangeSlider(
                    id='movie_rating_slider',
                    min=0.0, max=5.0, step=0.1, value=[0.0, 5.0],
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Br(),

                html.Label("Minimum Number of Movie Ratings"),
                dcc.RangeSlider(
                    id='movie_rating_count_slider',
                    min=0, max=vote_count_max, step=1, value=[0],
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Br(),

                dbc.Button("Apply Filters", id='apply_filters', color="primary", className="mt-2"),
                dbc.Button("Reset Filters", id="reset_filters", color="primary", className="mt-2", style={"marginLeft": "10px"})
            ], width=3),

            # analysis part
            dbc.Col([
                html.H3("Movie Rating Analysis", className="mb-4"),

                # graphs are ordered in a 2 x 2 grid
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        id='graph_genres',
                        figure=create_bar_chart(
                            df=pd.DataFrame({'main_genre': [], 'count': []}),
                            x_column='main_genre',
                            y_column='count',
                            title='Average Movie Rating by Genre'
                        )),
                            width=6),
                    dbc.Col(dcc.Graph(
                        id='graph_directors',
                        figure=create_bar_chart( 
                            df=pd.DataFrame({'director': [], 'count': []}),
                            x_column='director',
                            y_column='count',
                            title='Top 10 Directors by Average Rating'
                        )),
                            width=6),
                ]),

                dbc.Row([
                    dbc.Col(dcc.Graph(
                        id='graph_actors',
                        figure=create_bar_chart(
                            df=pd.DataFrame({'lead_actor': [], 'count': []}),
                            x_column='lead_actor',
                            y_column='count',
                            title='Top 10 Lead Actors by Average Rating'
                        )),
                            width=6),
                    dbc.Col(dcc.Graph(
                        id='graph_movies',
                        figure=create_bar_chart(
                            df=pd.DataFrame({'title': [], 'count': []}),
                            x_column='title',
                            y_column='count',
                            title='Top 10 Movies by Average Rating'
                        )),
                            width=6),
                ])
            ], width=9),

            # recommendation part
            html.H3("Movie Recommendation", className="mb-4"),

            # ordered in a 1 x 3 grid
            dbc.Row([
                dbc.Col(dcc.Graph(
                    id="graph_cluster"
                    ), 
                    width=12)
            ]),

            dbc.Row([
                dbc.Col(dcc.Graph(
                    id="graph_recs"), 
                    width=12)
            ]),

            dbc.Row([
                dbc.Col(dcc.Graph(
                    id="graph_watched"), 
                    width=12)
            ]),

            # for the users top recommended movies
            html.Div(id="recommended_movies_box", className="mt-4", style={"whiteSpace": "pre-wrap"}),

        ])
    ], fluid=True)
])



# Update graphs based on the filters, after pressing the apply filter button
@app.callback(
    Output("graph_genres", "figure"),
    Output("graph_directors", "figure"),
    Output("graph_actors", "figure"),
    Output("graph_movies", "figure"),
    Input("apply_filters", "n_clicks"),
    State("director_dropdown", "value"),
    State("actor_dropdown", "value"),
    State("genre_dropdown", "value"),
    State("language_dropdown", "value"),
    State("release_year_slider", "value"),
    State("movie_rating_slider", "value"),
    State("movie_rating_count_slider", "value")
)
def update_genre_graph(n_clicks, directors, actors, genres, languages, year_range, rating_range, vote_count_range):
    df_filtered = get_filtered_movies(df_movies, directors, actors, genres, languages, year_range, rating_range, vote_count_range)

    # Get the data for both graphs
    genre_avg = get_grouped_mean(df_filtered, "main_genre", "vote_average")
    df_genre_avg = genre_avg.reset_index()

    director_avg = get_grouped_mean(df_filtered, "director", "vote_average")
    df_director_avg = director_avg.nlargest(10).reset_index()

    actor_avg = get_grouped_mean(df_filtered, "lead_actor", "vote_average")
    df_actor_avg = actor_avg.nlargest(10).reset_index()

    df_movie_avg = df_filtered.sort_values(by="vote_average", ascending=False).head(10)

    # Genre graph
    fig_genres = create_bar_chart(
        df=df_genre_avg,
        x_column="main_genre",
        y_column="vote_average",
        title="Average Movie Rating by Genre",
        x_axis_title="Main Genre",
        y_axis_title="Average Rating",
        sort_by_y=True
    )

    # Director graph
    fig_directors = create_bar_chart(
        df=df_director_avg,
        x_column="director",
        y_column="vote_average",
        title="Top 10 Directors by Average Rating",
        x_axis_title="Director",
        y_axis_title="Average Rating",
        sort_by_y=True
    )

    # Actor graph
    fig_actors = create_bar_chart(
        df=df_actor_avg,
        x_column="lead_actor",
        y_column="vote_average",
        title="Top 10 Lead Actors by Average Rating",
        x_axis_title="Lead Actor",
        y_axis_title="Average Rating",
        sort_by_y=True
    )

    # Movie graph
    fig_movies = create_bar_chart(
        df=df_movie_avg,
        x_column="title",
        y_column="vote_average",
        title="Top 10 Movies by Average Rating",
        x_axis_title="Movie Title",
        y_axis_title="Average Rating",
        sort_by_y=True
    )

    return fig_genres, fig_directors, fig_actors, fig_movies


# Update filters based on clickData from graphs, as well as on the reset button
@app.callback(
    Output("director_dropdown", "value"),
    Output("actor_dropdown", "value"),
    Output("genre_dropdown", "value"),
    Output("language_dropdown", "value"),
    Output("release_year_slider", "value"),
    Output("movie_rating_slider", "value"),
    Output("movie_rating_count_slider", "value"),
    Input("reset_filters", "n_clicks"),
    Input('graph_genres', 'clickData'),
    Input('graph_directors', 'clickData'),
    Input('graph_actors', 'clickData'),
    State("director_dropdown", "value"),
    State("actor_dropdown", "value"),
    State("genre_dropdown", "value"),
    prevent_initial_call=True
)
def update_filters(reset_clicks, click_genre, click_director, click_actor,
                   current_directors, current_actors, current_genres):
    ctx = callback_context
    triggered = ctx.triggered[0]['prop_id'].split('.')[0]

    # Default values
    current_directors = current_directors or []
    current_actors = current_actors or []
    current_genres = current_genres or []

    # On button press, reset everything
    if triggered == 'reset_filters':
        return None, None, None, None, [year_min, year_max], [0.0, 5.0], [0]

    elif triggered == 'graph_genres' and click_genre:
        clicked_genre = click_genre['points'][0]['x']
        if clicked_genre not in current_genres:
            current_genres = current_genres + [clicked_genre]

    elif triggered == 'graph_directors' and click_director:
        clicked_director = click_director['points'][0]['x']
        if clicked_director not in current_directors:
            current_directors = current_directors + [clicked_director]

    elif triggered == 'graph_actors' and click_actor:
        clicked_actor = click_actor['points'][0]['x']
        if clicked_actor not in current_actors:
            current_actors = current_actors + [clicked_actor]

    # If not reset (through the button), just return updated filters with the new selection
    return current_directors, current_actors, current_genres, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# Provide the selected users top movies (from the dropdown menu)
# Using the filtered selections
@app.callback(
    Output("graph_cluster", "figure"),
    Output("graph_recs", "figure"),
    Output("graph_watched", "figure"),
    Output("recommended_movies_box", "children"),
    Input("user_dropdown", "value"),
    Input("apply_filters", "n_clicks"),
    State("director_dropdown", "value"),
    State("actor_dropdown", "value"),
    State("genre_dropdown", "value"),
    State("language_dropdown", "value"),
    State("release_year_slider", "value"),
    State("movie_rating_slider", "value"),
    State("movie_rating_count_slider", "value")
)
def generate_recommendations(user_id_full, n_clicks,
                             directors, actors, genres, languages,
                             year_range, rating_range, vote_count_range):
    
    # Get user number in the correct format ('user_x' to x)
    user_id = int(user_id_full.split('_')[1])

    # Filter data
    df_filtered = get_filtered_movies(df_movies, directors, actors, genres, languages, year_range, rating_range, vote_count_range)

    # Get selected genres. If none are selected, it will use ALL genres
    if(not genres):
        genres = main_genres

    selected_genres = [genre2id[g] for g in genres] if genres else []
    filtered_pool = get_movie_pool(df_filtered, genre_ids=selected_genres)

    recs = recommend_movies_for_user(
        user_id=user_id,
        filtered_df=filtered_pool,
        df_ratings=df_ratings,
        df_users=df_users,
        n_recs=5,
        explain=True,
        overview_topic_cols=overview_topic_cols,
        topic_words=topic_words,
        tag_topic_cols=tag_topic_cols,
        tag_topic_words=tag_topic_words
    )

    # Get the special plot needed for the scatter and bar charts
    df_plot = get_plot_df(df_ratings, df_filtered, user_id, filtered_pool, recs)

    # Movie cluster graph
    fig_cluster = create_cluster_scatter_plot(
        df=df_filtered,
        x='pca_1',
        y='pca_2',
        color='movie_cluster',
        title='Movie Clusters in PCA Space'
    )
    
    # Recommended movies in the cluster graph
    fig_recs = create_recomended_scatter_plot(
        df = df_plot,
        x='pca_1', 
        y='pca_2',
        color='status',
        symbol='status',
        size='rating',
        title='Watched & Recommended Movies for User 4 in Feature Space'
    )

    # Watched vs recommended chart
    fig_watched = create_bar_recs_plot(
        df = df_plot,
        x='main_genre', 
        y='rating', 
        color='status',
        title='Watched vs Recommended: Average Rating per Genre'
    )

    recommendations_card = html.Pre("\n".join([f"Recommended: {rec['title']}\nWhy: {rec['explanation']}\n" for rec in recs]))

    return fig_cluster, fig_recs, fig_watched, recommendations_card



# Run the app
if __name__ == "__main__":
    app.run(debug=True)