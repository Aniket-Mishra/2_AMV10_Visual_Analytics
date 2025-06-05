import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from common_functions import * 

# get data
df_movies = pd.read_parquet('processed_data/movies_data_updated.parquet')

# get min and max year for slider
year_min_max = get_column_min_max(df_movies, 'release_year')
year_min = year_min_max['min_value']
year_max = year_min_max['max_value']

# get list of directors
directors = df_movies['director'].dropna().unique()
directors = sorted(directors) # sort the list 

# get list of genres
main_genres = df_movies['main_genre'].dropna().unique()
main_genres = sorted(main_genres) # sort the list 






# actual app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Movie Recommendations"

# layout page 1 (movie analysis)
app.layout = html.Div([
    
    # navbar (for user and going to second page)
    dbc.NavbarSimple(
        children=[
            dbc.Button("Recommendations", color="secondary", href="#", disabled=True, 
                       style={'width': '150px', 'margin-right': '10px'}),
            dcc.Dropdown(
                id='user-dropdown',
                options=[{'label': f'User {i}', 'value': f'user_{i}'} for i in range(1, 3)],
                value='user_1',
                style={'width': '150px'}
            )
        ],
        brand="Movie Rating Analysis",
        color="primary",
        dark=True,
        className="mb-4"
    ),

    dbc.Container([

        dbc.Row([

            # sidebar filter
            dbc.Col([
                html.H5("Filters", className="mb-3"),

                html.Label("Directors:"),
                dcc.Dropdown(
                    id='director_dropdown',
                    options=[{'label': director, 'value': director} for director in directors],
                    value=None, multi=True,
                    placeholder="Select a director...",
                ),
                html.Br(),

                html.Label("Main genres:"),
                dcc.Dropdown(
                    id='genre_dropdown',
                    options=[{'label': genre, 'value': genre} for genre in main_genres],
                    value=None, multi=True,
                    placeholder="Select a main genre...",
                ),
                html.Br(),

                html.Label("Movie release year:"),
                dcc.RangeSlider(
                    id='release_year_slider',
                    min=year_min, max=year_max, step=1, value=[year_min, year_max],
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Br(),

                html.Label("Movie rating:"),
                dcc.RangeSlider(
                    id='movie_rating_slider',
                    min=0.0, max=5.0, step=0.1, value=[0.0, 5.0],
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Br(),

                dbc.Button("Apply Filters", id='apply_filters', color="primary", className="mt-2"),
                dbc.Button("Reset Filters", id="reset_filters", color="primary", className="mt-2", style={"marginLeft": "10px"})
            ], width=3),

            # graphs
            dbc.Col([

                # ordered in a 2 x 2 'grid'
                dbc.Row([
                    dbc.Col(html.Div("Graph 1: genres", className="p-3 bg-light border rounded text-center"), width=6),
                    dbc.Col(html.Div("Graph 2: directors", className="p-3 bg-light border rounded text-center"), width=6),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col(html.Div("Graph 3: lead actors", className="p-3 bg-light border rounded text-center"), width=6),
                    dbc.Col(html.Div("Graph 4: top movies", className="p-3 bg-light border rounded text-center"), width=6),
                ])
            ], width=9)

        ])
    ], fluid=True)
])



@app.callback(
    Output("director_dropdown", "value"),
    Output("genre_dropdown", "value"),
    Output("release_year_slider", "value"),
    Output("movie_rating_slider", "value"),
    Input("reset_filters", "n_clicks"),
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    year_min_max = get_column_min_max(df_movies, "release_year")
    year_min = year_min_max['min_value']
    year_max = year_min_max['max_value']
    
    return None, None, [year_min, year_max], [0.0, 5.0]

# Run the app
if __name__ == "__main__":
    app.run(debug=True)