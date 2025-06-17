# functions.py

import json
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html

def load_data():
    df_movies = pd.read_parquet("../data/1_movies_data_for_app.parquet")
    df_users = pd.read_parquet("../data/1_all_users_stats_with_clusters.parquet")
    df_ratings = pd.read_parquet("../data/1_ratings_data_filtered.parquet")

    users_for_app = {8547: "Aniket", 265550: "Rose", 276879: "Prof", 270637: "Pakhi"}

    with open('../data/topic_words.json', 'r') as f:
        topic_dicts = json.load(f)
        topic_words = {int(k): v for k, v in topic_dicts['overview_topic_words'].items()}
        tag_topic_words = {int(k): v for k, v in topic_dicts['tag_topic_words'].items()}
        keywords_topic_words = {int(k): v for k, v in topic_dicts['keywords_topic_words'].items()}

    all_genres_from_list = set(g for genres in df_movies['genre_list'] for g in genres)
    all_genres_from_main = set(df_movies['main_genre'].dropna().unique())
    all_genres = all_genres_from_list | all_genres_from_main
    genre2id = {genre: idx for idx, genre in enumerate(sorted(all_genres))}
    id2genre = {idx: genre for genre, idx in genre2id.items()}

    all_directors = df_movies['director'].dropna().unique()
    director2id = {director: idx for idx, director in enumerate(sorted(all_directors))}
    id2director = {idx: director for idx, director in director2id.items()}

    all_actors = df_movies['lead_actor'].dropna().unique()
    actor2id = {actor: idx for idx, actor in enumerate(sorted(all_actors))}
    id2actor = {idx: actor for actor, idx in actor2id.items()}

    overview_topic_cols = [col for col in df_movies.columns if col.startswith("overview_topic_")]
    tag_topic_cols = [col for col in df_movies.columns if col.startswith("tag_topic_")]

    return (
        df_movies, df_users, df_ratings,
        users_for_app, topic_words, tag_topic_words, keywords_topic_words,
        genre2id, id2genre, director2id, id2director, actor2id, id2actor,
        overview_topic_cols, tag_topic_cols
    )

def build_header(users_for_app, selected_page, selected_stat_type, selected_user):
    """Reusable navbar/header with navigation and filters."""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.H2("Movie Recommendations", className="mb-0 text-white"), width="auto"),
                dbc.Col(dbc.Button("Movies", id="btn-movies", color="primary", outline=selected_page != "movies", className="mx-1")),
                dbc.Col(dbc.Button("Recommendations", id="btn-recommendations", color="primary", outline=selected_page != "recommendations", className="mx-1")),
                dbc.Col([
                    dcc.Dropdown(
                        id="stat-type-dropdown",
                        options=[{"label": "Global Stats", "value": "Global"}, {"label": "User Stats", "value": "User"}],
                        value=selected_stat_type,
                        clearable=False,
                        style={"width": "150px", "display": "inline-block"}
                    )
                ], width="auto", className="mx-2"),
                dbc.Col([
                    dcc.Dropdown(
                        id="user-dropdown",
                        options=[{"label": name, "value": uid} for uid, name in users_for_app.items()],
                        value=selected_user,
                        clearable=False,
                        style={"width": "150px", "display": "inline-block"}
                    )
                ], width="auto", className="mx-2"),
                dbc.Col(dbc.Button("Reset Filters", id="btn-reset-filters", color="secondary", className="mx-1")),
                dbc.Col(dbc.Button("Reset App", id="btn-reset-app", color="danger", className="mx-1")),
            ], align="center", className="g-2"),
        ]),
        color="dark",
        dark=True,
        className="mb-3"
    )

def build_kpi_section(
    df_movies, df_ratings, user_id,
    filtered_df_movies=None, filtered_df_user_movies=None,
    show_details=False
):
    """Reusable KPI display for global/user stats (total & filtered)."""
    # If not provided, filtered is the same as unfiltered for now
    if filtered_df_movies is None:
        filtered_df_movies = df_movies
    user_rated_movies = df_ratings[df_ratings["userId"] == user_id]["movieId"].unique()
    df_user_movies = df_movies[df_movies["movieId"].isin(user_rated_movies)]
    if filtered_df_user_movies is None:
        filtered_df_user_movies = df_user_movies

    # 1. Global Stats (all)
    n_movies_global = df_movies.shape[0]
    total_votes_global = int(df_movies['vote_count'].sum())
    avg_votes_global = round(df_movies['vote_average'].mean(), 2)
    top3_genres_global = df_movies['main_genre'].value_counts().head(3).index.tolist()

    # 2. Global Stats (filtered)
    n_movies_global_f = filtered_df_movies.shape[0]
    total_votes_global_f = int(filtered_df_movies['vote_count'].sum())
    avg_votes_global_f = round(filtered_df_movies['vote_average'].mean(), 2)
    top3_genres_global_f = filtered_df_movies['main_genre'].value_counts().head(3).index.tolist()

    # 3. User Stats (all)
    n_movies_user = df_user_movies.shape[0]
    total_votes_user = int(df_user_movies['vote_count'].sum())
    avg_votes_user = round(df_user_movies['vote_average'].mean(), 2) if n_movies_user > 0 else 0
    top3_genres_user = df_user_movies['main_genre'].value_counts().head(3).index.tolist()

    # 4. User Stats (filtered)
    n_movies_user_f = filtered_df_user_movies.shape[0]
    total_votes_user_f = int(filtered_df_user_movies['vote_count'].sum())
    avg_votes_user_f = round(filtered_df_user_movies['vote_average'].mean(), 2) if n_movies_user_f > 0 else 0
    top3_genres_user_f = filtered_df_user_movies['main_genre'].value_counts().head(3).index.tolist()

    # return dbc.Row([
    #     dbc.Col(
    #         dbc.Card([
    #             dbc.CardHeader("Global Stats (Total)"),
    #             dbc.CardBody([
    #                 html.P(f"Movies: {n_movies_global}"),
    #                 html.P(f"Total Votes: {total_votes_global}"),
    #                 html.P(f"Average Vote: {avg_votes_global}"),
    #                 html.P(f"Top 3 Genres: {', '.join(top3_genres_global)}"),
    #             ])
    #         ]), width=3
    #     ),
    #     dbc.Col(
    #         dbc.Card([
    #             dbc.CardHeader("Global Stats (Filtered)"),
    #             dbc.CardBody([
    #                 html.P(f"Movies: {n_movies_global_f}"),
    #                 html.P(f"Total Votes: {total_votes_global_f}"),
    #                 html.P(f"Average Vote: {avg_votes_global_f}"),
    #                 html.P(f"Top 3 Genres: {', '.join(top3_genres_global_f)}"),
    #             ])
    #         ]), width=3
    #     ),
    #     dbc.Col(
    #         dbc.Card([
    #             dbc.CardHeader("User Stats (Total)"),
    #             dbc.CardBody([
    #                 html.P(f"Movies: {n_movies_user}"),
    #                 html.P(f"Total Votes: {total_votes_user}"),
    #                 html.P(f"Average Vote: {avg_votes_user}"),
    #                 html.P(f"Top 3 Genres: {', '.join(top3_genres_user)}"),
    #             ])
    #         ]), width=3
    #     ),
    #     dbc.Col(
    #         dbc.Card([
    #             dbc.CardHeader("User Stats (Filtered)"),
    #             dbc.CardBody([
    #                 html.P(f"Movies: {n_movies_user_f}"),
    #                 html.P(f"Total Votes: {total_votes_user_f}"),
    #                 html.P(f"Average Vote: {avg_votes_user_f}"),
    #                 html.P(f"Top 3 Genres: {', '.join(top3_genres_user_f)}"),
    #             ])
    #         ]), width=3
    #     ),
    # ], className="mb-4 g-4")
    card_bodies = [
        [
            html.P(f"Movies: {n_movies_global}"),
            html.P(f"Total Votes: {total_votes_global}"),
            html.P(f"Average Vote: {avg_votes_global}"),
            html.P(f"Top 3 Genres: {', '.join(top3_genres_global)}"),
        ],
        [
            html.P(f"Movies: {n_movies_global_f}"),
            html.P(f"Total Votes: {total_votes_global_f}"),
            html.P(f"Average Vote: {avg_votes_global_f}"),
            html.P(f"Top 3 Genres: {', '.join(top3_genres_global_f)}"),
        ],
        [
            html.P(f"Movies: {n_movies_user}"),
            html.P(f"Total Votes: {total_votes_user}"),
            html.P(f"Average Vote: {avg_votes_user}"),
            html.P(f"Top 3 Genres: {', '.join(top3_genres_user)}"),
        ],
        [
            html.P(f"Movies: {n_movies_user_f}"),
            html.P(f"Total Votes: {total_votes_user_f}"),
            html.P(f"Average Vote: {avg_votes_user_f}"),
            html.P(f"Top 3 Genres: {', '.join(top3_genres_user_f)}"),
        ],
    ]

    card_headers = [
        "Global Stats (Total)",
        "Global Stats (Filtered)",
        "User Stats (Total)",
        "User Stats (Filtered)",
    ]

    return dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    dbc.Button(
                        card_headers[i],
                        id={"type": "kpi-header", "index": i},
                        n_clicks=0,
                        color="secondary",  # This gives a gray background (matches Bootstrap)
                        style={
                            "textAlign": "left",
                            "width": "100%",
                            "padding": "0.75rem 1.25rem",  # Bootstrap card header padding
                            "fontWeight": "bold",
                            "backgroundColor": "#f7f7f9",  # Optional: matches Bootstrap card-header
                            "border": "none",
                            "boxShadow": "none",
                            "color": "#212529",  # Standard Bootstrap text color
                            "fontSize": "1rem",
                            "outline": "none",
                            "cursor": "pointer",
                        },
                        className="card-header"
                    ),
                    style={"padding": 0}
                ),
                dbc.CardBody(card_bodies[i]) if show_details else None
            ]),
            width=3,
        )
        for i in range(4)
    ], className="mb-4 g-4")


def movies_page_layout():
    """Placeholder for Movies analysis page."""
    return html.Div([
        html.H3("Movie Analysis Page"),
        html.P("Put your Movie analysis charts, plots, and explanations here."),
        # Future: Insert more filters/graphs here!
    ])

def recommendations_page_layout():
    """Placeholder for Recommendations page."""
    return html.Div([
        html.H3("Movie Recommendations Page"),
        html.P("Put your Recommendation engine outputs and explanations here."),
        # Future: Insert rec components here!
    ])
    
def build_filters(
    all_directors, all_actors, all_genres,
    director_value=None, actor_value=None, genre_value=None,
    rating_range=(0, 5)
):
    return dbc.Row([
        # --- Director Filter ---
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Label("Directors"), width="auto"),
                dbc.Col(
                    [
                        dbc.Button("Show Selected", id="show-selected-directors-btn", color="secondary", size="sm", className="me-2"),
                        dbc.Button("Select All", id="select-all-directors", color="info", size="sm"),
                    ],
                    width="auto",
                    style={"textAlign": "right"}
                ),
            ], justify="between", align="center", className="mb-1"),
            dcc.Dropdown(
                id="director-dropdown",
                options=[{"label": d, "value": d} for d in sorted(all_directors)],
                value=director_value if director_value else [],
                multi=True,
                placeholder="Select director(s)",
            ),
            # NEW: Modal to show all selected directors
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Selected Directors")),
                dbc.ModalBody(id="selected-directors-list"),
            ], id="modal-directors", is_open=False),
        ], width=3),

        # --- Actor Filter ---
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Label("Lead Actors"), width="auto"),
                dbc.Col(
                    [
                        dbc.Button("Show Selected", id="show-selected-actors-btn", color="secondary", size="sm", className="me-2"),
                        dbc.Button("Select All", id="select-all-actors", color="info", size="sm"),
                    ],
                    width="auto",
                    style={"textAlign": "right"}
                ),
            ], justify="between", align="center", className="mb-1"),
            dcc.Dropdown(
                id="actor-dropdown",
                options=[{"label": a, "value": a} for a in sorted(all_actors)],
                value=actor_value if actor_value else [],
                multi=True,
                placeholder="Select actor(s)",
            ),
            # NEW: Modal to show all selected actors
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Selected Actors")),
                dbc.ModalBody(id="selected-actors-list"),
            ], id="modal-actors", is_open=False),
        ], width=3),

        # --- Genre Filter ---
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Label("Main Genres"), width="auto"),
                 dbc.Col(
                    [
                        dbc.Button("Show Selected", id="show-selected-genres-btn", color="secondary", size="sm", className="me-2"),
                        dbc.Button("Select All", id="select-all-genres", color="info", size="sm"),
                    ],
                    width="auto",
                    style={"textAlign": "right"}
                ),
            ], justify="between", align="center", className="mb-1"),
            dcc.Dropdown(
                id="genre-dropdown",
                options=[{"label": g, "value": g} for g in sorted(all_genres)],
                value=genre_value if genre_value else [],
                multi=True,
                placeholder="Select genre(s)",
            ),
            # NEW: Modal to show all selected genres
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Selected Genres")),
                dbc.ModalBody(id="selected-genres-list"),
            ], id="modal-genres", is_open=False),
        ], width=3),

        # --- Rating Slider ---
        dbc.Col([
            html.Label("Movie Rating"),
            dcc.RangeSlider(
                id="rating-slider", min=0, max=5, step=0.5,
                marks={i / 2: str(i / 2) for i in range(0, 11)},
                value=rating_range if rating_range else [0, 5],
                tooltip={"placement": "bottom", "always_visible": False},
            )
        ], width=3)
    ], className="mb-4 g-4")