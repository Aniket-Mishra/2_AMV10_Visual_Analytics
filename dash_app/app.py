import dash
from dash import dcc, html, Input, Output, State, ctx, no_update, ALL, callback_context, ctx
import dash_bootstrap_components as dbc
import re
from functions import *
from common_functions import *

def parse_explanation(exp):
    genre = users = acclaimed = themes = ""

    # Genre
    match = re.search(r"Matches your favorite genre \((.*?)\)", exp)
    if match:
        genre = match.group(1)

    # Users
    users = "Yes" if "Popular among other users" in exp else ""
    
    # Critically acclaimed
    acclaimed = "Yes" if "Critically acclaimed" in exp else ""
    
    # Movie Themes (everything after 'Notable themes:')
    themes_match = re.search(r"Notable themes: (.*)", exp)
    if themes_match:
        themes = themes_match.group(1).strip()

    return genre, users, acclaimed, themes

def make_recommendations_table(recs):
    if not recs:
        return html.Div("No recommendations found.", style={"fontStyle": "italic", "color": "#999"})

    header = html.Thead(html.Tr([
        html.Th("#"),
        html.Th("Title"),
        html.Th("Genre"),
        html.Th("Users"),
        html.Th("Acclaimed"),
        html.Th("Movie Themes"),
    ]))

    body = html.Tbody([
        html.Tr([
            html.Td(i + 1),
            html.Td(rec["title"]),
            html.Td(parse_explanation(rec["explanation"])[0]),
            html.Td(parse_explanation(rec["explanation"])[1]),
            html.Td(parse_explanation(rec["explanation"])[2]),
            html.Td(parse_explanation(rec["explanation"])[3]),
        ])
        for i, rec in enumerate(recs)
    ])

    return dbc.Table([header, body], bordered=True, striped=True, hover=True, responsive=True)

def get_selected_points(selected_data, key1="label", key2="x", fallback="customdata"):
    if not selected_data or "points" not in selected_data:
        return []
    out = []
    for pt in selected_data["points"]:
        if key1 in pt:
            out.append(pt[key1])
        elif key2 in pt:
            out.append(pt[key2])
        elif fallback in pt:
            if isinstance(pt[fallback], list):
                out.append(pt[fallback][0])
            else:
                out.append(pt[fallback])
    return out

(
    df_movies, df_users, df_ratings,
    users_for_app, topic_words, tag_topic_words, keywords_topic_words,
    genre2id, id2genre, director2id, id2director, actor2id, id2actor,
    overview_topic_cols, tag_topic_cols
) = load_data()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)
app.title = "Movie Recommendations"
server = app.server

DEFAULT_USER_ID = list(users_for_app.keys())[0]
DEFAULT_STAT_TYPE = "Global"
DEFAULT_PAGE = "movies"

# --- Sliders: min/max for the dataset ---
year_min, year_max = df_movies['release_year'].min(), df_movies['release_year'].max()
votes_min, votes_max = df_movies['vote_count'].min(), df_movies['vote_count'].max()

# --- App Layout ---
app.layout = html.Div(className="main-app-container",
                      children=[
                            dcc.Store(id="current-page", data=DEFAULT_PAGE),
                            # dcc.Store(id="selected-stat-type", data=DEFAULT_STAT_TYPE),
                            dcc.Store(id="selected-user", data=DEFAULT_USER_ID),
                            dcc.Store(id="show-kpi-details", data=False),
                            dcc.Store(id="kpi-header-clicks", data=[0, 0, 0, 0]),
                            dcc.Store(id='genres-selected-store', data=None),
                            dcc.Store(id='directors-selected-store', data=None),
                            dcc.Store(id='actors-selected-store', data=None),
                            dcc.Store(id='movies-selected-store', data=None),


                            html.Div(id="header-div"),

                            build_filters(
                                all_directors=get_column_unique_values(df_movies, 'director'),
                                all_actors=get_column_unique_values(df_movies, 'lead_actor'),
                                all_genres=get_column_unique_values(df_movies, 'main_genre'),
                                director_value=None,
                                actor_value=None,
                                genre_value=None,
                                rating_range=[0,5],
                                year_range=(year_min, year_max),
                                year_value=[year_min, year_max],
                                votes_range=(votes_min, votes_max),
                                votes_value=[votes_min, votes_max],
                            ),
                            html.Div(id="kpi-div"),
                            html.Div([
                                # Movies page graphs
                                html.Div(id="movies-graphs-div", children=movies_page_layout(), style={'display': 'block'}),
                                # Recommendations page graphs
                                html.Div(id="recs-graphs-div", children=recommendations_page_layout(), style={'display': 'none'}),
                            ], id="page-content-div")

                    ])


@app.callback(
    Output("kpi-div", "children"),
    Output("page-content-div", "children"),
    Input("current-page", "data"),
    Input("selected-user", "data"),
    Input("director-dropdown", "value"),
    Input("actor-dropdown", "value"),
    Input("genre-dropdown", "value"),
    Input("rating-slider", "value"),
    Input("year-slider", "value"),
    Input("votes-slider", "value"),
    Input("show-kpi-details", "data"),
)
def render_app(
    selected_page, selected_user,
    director_values, actor_values, genre_values, rating_range,
    year_range, votes_range, show_kpi_details
):
    # Start with all movies
    filtered_df_movies = df_movies.copy()

    # Director filter
    if director_values:
        filtered_df_movies = filtered_df_movies[filtered_df_movies['director'].isin(director_values)]
    # Actor filter
    if actor_values:
        filtered_df_movies = filtered_df_movies[filtered_df_movies['lead_actor'].isin(actor_values)]
    # Genre filter
    if genre_values:
        filtered_df_movies = filtered_df_movies[filtered_df_movies['main_genre'].isin(genre_values)]
    # Rating range filter
    min_rating, max_rating = (0, 5)
    if isinstance(rating_range, (list, tuple)) and len(rating_range) == 2:
        min_rating, max_rating = rating_range
        filtered_df_movies = filtered_df_movies[
            (filtered_df_movies['vote_average'] >= min_rating) &
            (filtered_df_movies['vote_average'] <= max_rating)
        ]
    # Year range filter (NEW)
    min_year, max_year = (year_min, year_max)
    if isinstance(year_range, (list, tuple)) and len(year_range) == 2:
        min_year, max_year = year_range
        filtered_df_movies = filtered_df_movies[
            (filtered_df_movies['release_year'] >= min_year) &
            (filtered_df_movies['release_year'] <= max_year)
        ]
    # Votes range filter (NEW)
    min_votes, max_votes = (votes_min, votes_max)
    if isinstance(votes_range, (list, tuple)) and len(votes_range) == 2:
        min_votes, max_votes = votes_range
        filtered_df_movies = filtered_df_movies[
            (filtered_df_movies['vote_count'] >= min_votes) &
            (filtered_df_movies['vote_count'] <= max_votes)
        ]

    # Filtered user movies
    user_rated_movies = df_ratings[df_ratings["userId"] == selected_user]["movieId"].unique()
    df_user_movies = df_movies[df_movies["movieId"].isin(user_rated_movies)]
    filtered_df_user_movies = filtered_df_movies[filtered_df_movies["movieId"].isin(user_rated_movies)]

    kpi_section = build_kpi_section(
        df_movies, df_ratings, selected_user,
        filtered_df_movies=filtered_df_movies,
        filtered_df_user_movies=filtered_df_user_movies,
        show_details=show_kpi_details
    )

    if selected_page == "movies":
        content = movies_page_layout()
    else:
        content = recommendations_page_layout()

    # return kpi_section, content
    return kpi_section, no_update


# --- Page Navigation ---
@app.callback(
    Output("current-page", "data"),
    Input("btn-movies", "n_clicks"),
    Input("btn-recommendations", "n_clicks"),
    Input("btn-reset-app", "n_clicks"),
    prevent_initial_call=True
)
def switch_page(btn_movies, btn_recommendations, btn_reset_app):
    trigger = ctx.triggered_id
    if trigger == "btn-movies" or trigger == "btn-reset-app":
        return "movies"
    elif trigger == "btn-recommendations":
        return "recommendations"
    return dash.no_update


@app.callback(
    Output("selected-user", "data"),
    Output("user-dropdown", "value"),
    Input("user-dropdown", "value"),
    Input("btn-reset-app", "n_clicks"),
    State("selected-user", "data"),
    prevent_initial_call=True
)
def update_user(user_id, n_reset_app, current_user):
    trigger = ctx.triggered_id
    if trigger == "btn-reset-app":
        return DEFAULT_USER_ID, DEFAULT_USER_ID
    elif trigger == "user-dropdown":
        return user_id, no_update
    return current_user, no_update


# Updating the dropdown and slider values based on selected movies, reset button and brushing
@app.callback(
    Output("director-dropdown", "value"),
    Output("actor-dropdown", "value"),
    Output("genre-dropdown", "value"),
    Output("rating-slider", "value"),
    Output("year-slider", "value"),
    Output("votes-slider", "value"),
    Input("btn-reset-filters", "n_clicks"),
    Input("btn-reset-app", "n_clicks"),
    Input("select-all-directors", "n_clicks"),
    Input("select-all-actors", "n_clicks"),
    Input("select-all-genres", "n_clicks"),
    Input('graph_directors', 'selectedData'),
    Input('graph_actors', 'selectedData'),
    Input('graph_directors', 'clickData'),
    Input('graph_actors', 'clickData'),
    State("director-dropdown", "options"),
    State("actor-dropdown", "options"),
    State("genre-dropdown", "options"),
    State("year-slider", "min"),
    State("year-slider", "max"),
    State("votes-slider", "min"),
    State("votes-slider", "max"),
    State("director-dropdown", "value"),
    State("actor-dropdown", "value"),
    State("genre-dropdown", "value"),
    prevent_initial_call=True
)
def handle_dropdowns(
    reset_filters_click, reset_app_click,
    select_all_directors_click, select_all_actors_click, select_all_genres_click,
    select_directors, select_actors, click_director, click_actor, director_options, actor_options, genre_options,
    year_min_slider, year_max_slider, votes_min_slider, votes_max_slider,
    current_directors, current_actors, current_genres
):
    trigger = ctx.triggered_id

    # Default values
    current_directors = current_directors or []
    current_actors = current_actors or []

    if trigger in ("btn-reset-filters", "btn-reset-app"):
        return [], [], [], [0, 5], [year_min_slider, year_max_slider], [votes_min_slider, votes_max_slider]
    elif trigger == "select-all-directors":
        return [opt["value"] for opt in director_options], dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    elif trigger == "select-all-actors":
        return dash.no_update, [opt["value"] for opt in actor_options], dash.no_update, dash.no_update, dash.no_update, dash.no_update
    elif trigger == "select-all-genres":
        return dash.no_update, dash.no_update, [opt["value"] for opt in genre_options], dash.no_update, dash.no_update, dash.no_update
    
    # Implement brushing for the bar charts
    # Get all directors from the selected data
    if trigger == 'graph_directors' and select_directors:
        selected_directors = [point['x'] for point in select_directors['points']]
        current_directors = current_directors + selected_directors
        return current_directors, current_actors, current_genres, dash.no_update, dash.no_update, dash.no_update
    # Get single director from the clicked bar
    elif trigger == 'graph_directors' and click_director:
        clicked_director = click_director['points'][0]['x']
        if clicked_director not in current_directors:
            current_directors = current_directors + [clicked_director]
        return current_directors, current_actors, current_genres, dash.no_update, dash.no_update, dash.no_update
    # Get all lead actors from the selected data
    elif trigger == 'graph_actors' and select_actors:
        selected_actors = [point['x'] for point in select_actors['points']]
        current_actors = current_actors + selected_actors
        return current_directors, current_actors, current_genres, dash.no_update, dash.no_update, dash.no_update
    # Get single lead actor from the clicked bar
    elif trigger == 'graph_actors' and click_actor:
        clicked_actor = click_actor['points'][0]['x']
        if clicked_actor not in current_actors:
            current_actors = current_actors + [clicked_actor]
        return current_directors, current_actors, current_genres, dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# --- Director Modal ---
@app.callback(
    Output("modal-directors", "is_open"),
    Output("selected-directors-list", "children"),
    Input("show-selected-directors-btn", "n_clicks"),
    Input("modal-directors", "is_open"),
    State("director-dropdown", "value"),
    prevent_initial_call=True,
)
def toggle_director_modal(show_clicks, is_open, selected):
    trigger = dash.callback_context.triggered_id
    if trigger == "show-selected-directors-btn":
        # Open modal and show list
        if selected:
            return True, html.Ul([html.Li(str(item)) for item in selected])
        else:
            return True, html.Div("No directors selected.")
    # Closing modal
    return False, dash.no_update

# --- Actor Modal ---
@app.callback(
    Output("modal-actors", "is_open"),
    Output("selected-actors-list", "children"),
    Input("show-selected-actors-btn", "n_clicks"),
    Input("modal-actors", "is_open"),
    State("actor-dropdown", "value"),
    prevent_initial_call=True,
)
def toggle_actor_modal(show_clicks, is_open, selected):
    trigger = dash.callback_context.triggered_id
    if trigger == "show-selected-actors-btn":
        if selected:
            return True, html.Ul([html.Li(str(item)) for item in selected])
        else:
            return True, html.Div("No actors selected.")
    return False, dash.no_update

# --- Genre Modal ---
@app.callback(
    Output("modal-genres", "is_open"),
    Output("selected-genres-list", "children"),
    Input("show-selected-genres-btn", "n_clicks"),
    Input("modal-genres", "is_open"),
    State("genre-dropdown", "value"),
    prevent_initial_call=True,
)
def toggle_genre_modal(show_clicks, is_open, selected):
    trigger = dash.callback_context.triggered_id
    if trigger == "show-selected-genres-btn":
        if selected:
            return True, html.Ul([html.Li(str(item)) for item in selected])
        else:
            return True, html.Div("No genres selected.")
    return False, dash.no_update

@app.callback(
    Output("show-kpi-details", "data"),
    Input({"type": "kpi-header", "index": ALL}, "n_clicks"),
    State("show-kpi-details", "data"),
    prevent_initial_call=True,
)
def toggle_kpi_details(n_clicks, currently_open):
    triggered = callback_context.triggered
    if triggered and any(x['value'] for x in triggered):
        return not currently_open
    return currently_open



@app.callback(
    [Output("graph_genres", "figure"),
     Output("graph_directors", "figure"),
     Output("graph_actors", "figure"),
     Output("graph_movies", "figure")],
    [Input("current-page", "data"),
     Input("director-dropdown", "value"),
     Input("actor-dropdown", "value"),
     Input("genre-dropdown", "value"),
     Input("rating-slider", "value"),
     Input("year-slider", "value"),
     Input("votes-slider", "value")]
)
def update_movies_graphs(page, directors, actors, genres, rating_range, year_range, vote_count_range):
    if page != "movies":
        return [go.Figure()] * 4 #5  # Empty figs if not movies page

    # Filter df_movies as in render_app
    df_filtered = df_movies.copy()
    if directors:
        df_filtered = df_filtered[df_filtered['director'].isin(directors)]
    if actors:
        df_filtered = df_filtered[df_filtered['lead_actor'].isin(actors)]
    if genres:
        df_filtered = df_filtered[df_filtered['main_genre'].isin(genres)]

    min_rating, max_rating = (0, 5)

    # Ratings
    if rating_range and len(rating_range) == 2:
        min_rating, max_rating = rating_range
        df_filtered = df_filtered[
            (df_filtered['vote_average'] >= min_rating) &
            (df_filtered['vote_average'] <= max_rating)
        ]
    min_year, max_year = (year_min, year_max)

    # Year range
    if year_range and len(year_range) == 2:
        min_year, max_year = year_range
        df_filtered = df_filtered[
            (df_filtered['release_year'] >= min_year) &
            (df_filtered['release_year'] <= max_year)
        ]
    min_votes, max_votes = (votes_min, votes_max)

    # Vote count
    if vote_count_range and len(vote_count_range) == 2:
        min_votes, max_votes = vote_count_range
        df_filtered = df_filtered[
            (df_filtered['vote_count'] >= min_votes) &
            (df_filtered['vote_count'] <= max_votes)
        ]

    # Create special dataframes to use for the plots
    genre_avg = get_grouped_mean(df_filtered, "main_genre", "vote_average")
    df_genre_avg = genre_avg.reset_index()

    director_avg = get_grouped_mean(df_filtered, "director", "vote_average")
    df_director_avg = director_avg.nlargest(10).reset_index()
    director_pop = get_grouped_mean(df_filtered, "director", "director_popularity") 
    df_director_pop = director_pop.reset_index().sort_values("director_popularity", ascending=False).head(10)

    actor_avg = get_grouped_mean(df_filtered, "lead_actor", "vote_average")
    df_actor_avg = actor_avg.nlargest(10).reset_index()
    actor_pop = get_grouped_mean(df_filtered, "lead_actor", "lead_actor_popularity")
    df_actor_pop = actor_pop.reset_index().sort_values("lead_actor_popularity", ascending=False).head(10)

    df_movie_avg = df_filtered.sort_values(by="vote_average", ascending=False).head(10)
    df_movie_pop = df_filtered.sort_values("popularity", ascending=True).tail(10)

    # Create figures, dynamic treemap and bar charts
    fig_genres = create_dynamic_treemap(
        df_filtered,
        "main_genre",
        title="Number of Movies by Genre"
    )

    fig_directors = create_bar_chart(
        df=df_director_pop,
        x_column="director",
        y_column="director_popularity",
        title="Top 10 Directors by Popularity",
        x_axis_title="Director",
        y_axis_title="Average Popularity",
        sort_by_y=True
    )

    fig_actors = create_bar_chart(
        df=df_actor_pop,
        x_column="lead_actor",
        y_column="lead_actor_popularity",
        title="Top 10 Lead Actors by Popularity",
        x_axis_title="Lead Actor",
        y_axis_title="Average Popularity",
        sort_by_y=True
    )

    fig_movies = create_bar_chart(
        df=df_movie_pop,
        x_column="title",
        y_column="popularity_score",
        title="Top 10 Movies by Popularity",
        x_axis_title="Movie Title",
        y_axis_title="Popularity",
        sort_by_y=True
    )

    fig_genres.update_layout(uirevision="movies-page")
    fig_directors.update_layout(uirevision="movies-page")
    fig_actors.update_layout(uirevision="movies-page")
    fig_movies.update_layout(uirevision="movies-page")
    return fig_genres, fig_directors, fig_actors, fig_movies


@app.callback(
    Output("graph_cluster", "figure"),
    Output("graph_recs", "figure"),
    Output("graph_watched", "figure"),
    Output("recommended_movies_box", "children"),
    Input("current-page", "data"),
    Input("selected-user", "data"),
    Input("director-dropdown", "value"),
    Input("actor-dropdown", "value"),
    Input("genre-dropdown", "value"),
    Input("rating-slider", "value"),
    Input("year-slider", "value"),
    Input("votes-slider", "value"),
)
def generate_recommendations(page, selected_user,
                             directors, actors, genres,
                             rating_range, year_range, vote_count_range):
    if page != "recommendations":
        return [go.Figure()] * 3 + [html.Div()]  # Empty if not recommendations

    user_id = int(selected_user) if isinstance(selected_user, str) and selected_user.isdigit() else selected_user

    # Start with all movies
    df_filtered = df_movies.copy()

    # 1. Director filter
    if directors and len(directors) > 0:
        df_filtered = df_filtered[df_filtered['director'].isin(directors)]
    # 2. Actor filter
    if actors and len(actors) > 0:
        df_filtered = df_filtered[df_filtered['lead_actor'].isin(actors)]
    # 3. Genre filter
    if genres and len(genres) > 0:
        df_filtered = df_filtered[df_filtered['main_genre'].isin(genres)]

    # 4. Rating filter
    min_rating, max_rating = 0, 5
    if isinstance(rating_range, (list, tuple)) and len(rating_range) == 2:
        min_rating, max_rating = rating_range
    df_filtered = df_filtered[
        (df_filtered['vote_average'] >= min_rating) &
        (df_filtered['vote_average'] <= max_rating)
    ]

    # 5. Year filter
    min_year, max_year = year_min, year_max
    if isinstance(year_range, (list, tuple)) and len(year_range) == 2:
        min_year, max_year = year_range
    df_filtered = df_filtered[
        (df_filtered['release_year'] >= min_year) &
        (df_filtered['release_year'] <= max_year)
    ]

    # 6. Votes filter
    min_votes, max_votes = votes_min, votes_max
    if isinstance(vote_count_range, (list, tuple)) and len(vote_count_range) == 2:
        min_votes, max_votes = vote_count_range
    df_filtered = df_filtered[
        (df_filtered['vote_count'] >= min_votes) &
        (df_filtered['vote_count'] <= max_votes)
    ]

    # ---------
    # Fallback: If filters yield empty, use all movies!
    if df_filtered.empty:
        df_filtered = df_movies.copy()

    # Pool by genres (if no genre filter, use all genres in the current filtered_df)
    if genres and len(genres) > 0:
        selected_genres = [genre2id[g] for g in genres if g in genre2id]
        filtered_pool = get_movie_pool(df_filtered, genre_ids=selected_genres)
    else:
        filtered_pool = get_movie_pool(df_filtered, genre_ids=None)  # All genres in current df

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

    df_plot = get_plot_df(df_ratings, df_filtered, user_id, filtered_pool, recs)

    # Create all the different figures: cluster, recs and watched
    fig_cluster = create_cluster_scatter_plot(
        df=df_filtered,
        x='pca_1',
        y='pca_2',
        color='movie_cluster',
        title='Movie Clusters in PCA Space'
    )

    fig_recs = create_recommended_scatter_plot(
        df = df_plot,
        x='pca_1', 
        y='pca_2',
        color='status',
        symbol='status',
        size='rating',
        title='Watched & Recommended Movies for User in Feature Space'
    )

    fig_watched = create_bar_recs_plot(
        df = df_plot,
        x='main_genre', 
        y='rating', 
        color='status',
        title='Watched vs Recommended: Rating per Genre'
    )

    recommendations_card = make_recommendations_table(recs)

    return fig_cluster, fig_recs, fig_watched, recommendations_card

@app.callback(
    Output("movies-graphs-div", "style"),
    Output("recs-graphs-div", "style"),
    Input("current-page", "data")
)
def show_correct_page(current_page):
    if current_page == "movies":
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}

@app.callback(
    Output("header-div", "children"),
    Input("current-page", "data"),
    State("selected-user", "data"),
)
def update_header(current_page, selected_user):
    return build_header(users_for_app, current_page, selected_user)

if __name__ == "__main__":
    app.run(debug=True, port=8801)
