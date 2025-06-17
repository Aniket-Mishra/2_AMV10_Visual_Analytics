# app.py

import dash
from dash import dcc, html, Input, Output, State, ctx, no_update, ALL, callback_context
import dash_bootstrap_components as dbc
from functions import *

(
    df_movies, df_users, df_ratings,
    users_for_app, topic_words, tag_topic_words, keywords_topic_words,
    genre2id, id2genre, director2id, id2director, actor2id, id2actor,
    overview_topic_cols, tag_topic_cols
) = load_data()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Movie Recommendations"
server = app.server

DEFAULT_USER_ID = list(users_for_app.keys())[0]
DEFAULT_STAT_TYPE = "Global"
DEFAULT_PAGE = "movies"

# --- App Layout ---
app.layout = html.Div([
    dcc.Store(id="current-page", data=DEFAULT_PAGE),
    dcc.Store(id="selected-stat-type", data=DEFAULT_STAT_TYPE),
    dcc.Store(id="selected-user", data=DEFAULT_USER_ID),
    dcc.Store(id="show-kpi-details", data=False),
    dcc.Store(id="kpi-header-clicks", data=[0, 0, 0, 0]),

    build_header(users_for_app, DEFAULT_PAGE, DEFAULT_STAT_TYPE, DEFAULT_USER_ID),

    html.Div(id="kpi-div"),

    build_filters(
        all_directors=df_movies['director'].dropna().unique(),
        all_actors=df_movies['lead_actor'].dropna().unique(),
        all_genres=df_movies['main_genre'].dropna().unique(),
        director_value=None,
        actor_value=None,
        genre_value=None,
        rating_range=[0,5]
    ),

    html.Div(id="page-content-div")
])


@app.callback(
    Output("kpi-div", "children"),
    Output("page-content-div", "children"),
    Input("current-page", "data"),
    Input("selected-stat-type", "data"),
    Input("selected-user", "data"),
    Input("director-dropdown", "value"),
    Input("actor-dropdown", "value"),
    Input("genre-dropdown", "value"),
    Input("rating-slider", "value"),
    Input("show-kpi-details", "data"),
)
def render_app(
    selected_page, selected_stat_type, selected_user,
    director_values, actor_values, genre_values, rating_range, show_kpi_details
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

    return kpi_section, content


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


# --- User/StatType/Filters: All in one! ---
@app.callback(
    Output("selected-user", "data"),
    Output("selected-stat-type", "data"),
    Input("user-dropdown", "value"),
    Input("stat-type-dropdown", "value"),
    Input("btn-reset-app", "n_clicks"),
    State("selected-user", "data"),
    State("selected-stat-type", "data"),
    prevent_initial_call=True
)
def update_user_and_stat_type(user_id, stat_type, n_reset_app, current_user, current_stat_type):
    trigger = ctx.triggered_id
    if trigger == "btn-reset-app":
        return DEFAULT_USER_ID, DEFAULT_STAT_TYPE
    elif trigger == "user-dropdown":
        return user_id, current_stat_type
    elif trigger == "stat-type-dropdown":
        return current_user, stat_type
    return current_user, current_stat_type


@app.callback(
    Output("director-dropdown", "value"),
    Output("actor-dropdown", "value"),
    Output("genre-dropdown", "value"),
    Output("rating-slider", "value"),
    Input("btn-reset-filters", "n_clicks"),
    Input("btn-reset-app", "n_clicks"),
    Input("select-all-directors", "n_clicks"),
    Input("select-all-actors", "n_clicks"),
    Input("select-all-genres", "n_clicks"),
    State("director-dropdown", "options"),
    State("actor-dropdown", "options"),
    State("genre-dropdown", "options"),
    prevent_initial_call=True
)
def handle_dropdowns(
    reset_filters_click, reset_app_click,
    select_all_directors_click, select_all_actors_click, select_all_genres_click,
    director_options, actor_options, genre_options
):
    trigger = ctx.triggered_id

    if trigger in ("btn-reset-filters", "btn-reset-app"):
        return [], [], [], [0, 5]

    if trigger == "select-all-directors":
        return [opt["value"] for opt in director_options], no_update, no_update, no_update
    if trigger == "select-all-actors":
        return no_update, [opt["value"] for opt in actor_options], no_update, no_update
    if trigger == "select-all-genres":
        return no_update, no_update, [opt["value"] for opt in genre_options], no_update

    return no_update, no_update, no_update, no_update




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
    return False, no_update

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
    return False, no_update

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
    return False, no_update

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


if __name__ == "__main__":
    app.run_server(debug=True)
