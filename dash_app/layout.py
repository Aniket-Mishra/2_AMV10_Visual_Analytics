# layout.py
import dash_core_components as dcc
import dash_html_components as html

def create_layout(available_genres, available_release_years, max_vote_count):
    """
    Creates the Dash app layout.

    Args:
        available_genres (list): Sorted list of unique main genres.
        available_release_years (list): Sorted list of unique release years.
        max_vote_count (int): Maximum vote count for the slider.

    Returns:
        html.Div: The main layout object.
    """
    min_year = min(available_release_years) if available_release_years else 1900
    max_year = max(available_release_years) if available_release_years else 2025
    year_marks = {year: str(year) for year in range(min_year, max_year + 1, max(1, int((max_year - min_year) / 10)))}
    vote_count_marks = {0: '0', 100: '100', 500: '500'}
    if max_vote_count > 1000: vote_count_marks[1000] = '1k'
    if max_vote_count > 5000: vote_count_marks[5000] = '5k'
    if max_vote_count > 10000: vote_count_marks[10000] = '10k'


    return html.Div([
        html.H1("Movie Data Visual Analytics"),

        # --- Control Panel ---
        html.Div([
            html.Div([
                html.Label("Select Main Genre:"),
                dcc.Dropdown(
                    id='genre-dropdown',
                    options=[{'label': genre, 'value': genre} for genre in available_genres],
                    value=None,
                    multi=True
                )
            ], style={'width': '48%', 'display': 'inline-block'}),

            html.Div([
                html.Label("Select Release Year Range:"),
                dcc.RangeSlider(
                    id='year-slider',
                    min=min_year,
                    max=max_year,
                    value=[min_year, max_year],
                    marks=year_marks,
                    step=1,
                    allowCross=False
                )
            ], style={'width': '48%', 'display': 'inline-block', 'paddingLeft': '2%'}),

             html.Div([
                html.Label("Minimum Vote Count:"),
                dcc.Slider(
                    id='vote-count-slider',
                    min=0,
                    max=max_vote_count,
                    value=10,
                    marks=vote_count_marks,
                    step=max(1, int(max_vote_count / 50)), # Dynamic step
                    tooltip={"placement": "bottom", "always_visible": True},
                )
            ], style={'width': '98%', 'paddingTop': '20px'}),

            # Add more filters here as needed

        ], style={'padding': '20px', 'border': '1px solid #d3d3d3', 'marginBottom': '20px'}),

        # --- Visualizations Area ---
        html.Div([
            dcc.Graph(id='movies-per-year-graph', style={'height': '400px'}),
            dcc.Graph(id='budget-revenue-scatter', style={'height': '400px'}),
            dcc.Graph(id='rating-by-genre-box', style={'height': '400px'}),
            # Add more dcc.Graph components here
        ])
    ])

# Example usage (if you want to test this module separately)
# if __name__ == '__main__':
#     # This part is just for testing the layout structure visually if needed
#     # It requires a minimal Dash app instance
#     app = dash.Dash(__name__)
#     app.layout = create_layout(
#         available_genres=['Action', 'Comedy', 'Drama', 'Unknown'],
#         available_release_years=[1990, 2000, 2010, 2020],
#         max_vote_count=20000
#     )
#     app.run_server(debug=True)