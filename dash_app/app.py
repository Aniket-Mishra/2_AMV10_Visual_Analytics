import ast
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from common_functions import get_top_n_values, get_grouped_aggregated_data

df = pd.read_parquet("../data/movies_filtered_cleaned.parquet")

numeric_cols = ['vote_average', 'vote_count', 'popularity_score', 'critical_success', 'crowd_approval']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

string_cols = ['title', 'director', 'lead_actor']
for col in string_cols:
    if col in df.columns:
        df[col] = df[col].astype(str)

df['score'] = (
    df['popularity_score'] * 0.4 +
    df['critical_success']  * 0.3 +
    df['crowd_approval']    * 0.3
)

def _parse_genres(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except ValueError:
            return []
    return []

df['genre_list'] = df['genre_list'].apply(_parse_genres)
df_exploded = df.explode('genre_list')
df_exploded = df_exploded[
    df_exploded['genre_list'].notnull() &
    (df_exploded['genre_list'] != '(no genres listed)')
]

df['release_date'] = pd.to_datetime(df['release_date'])

plotly_template = 'plotly_dark'
graph_titles = {
    'genre-radial-graph':    'Genre Distribution',
    'top-genres-votes-graph':'Top 5 Genres by Avg. Vote',
    'top-movies-votes-graph':'Top 5 Movies by Total Votes',
    'top-genres-score-graph':'Top Genres by Movie Count',
    'top-movies-score-graph':'Top 10 Movies by Overall Score',
    'director-graph':        'Top 10 Directors by Avg. Movie Score',
    'actor-graph':           'Top 10 Actors by Avg. Movie Score'
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

app.layout = dbc.Container([
    dcc.Store(id='filtered-data-store'),
    dbc.Row([
        dbc.Col(html.H1("🎬 Interactive Movie Dashboard",
                        className="text-center text-primary mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H5("Select Release Date Range", className="text-light"),
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=df['release_date'].min().date(),
                max_date_allowed=df['release_date'].max().date(),
                start_date=df['release_date'].min().date(),
                end_date=df['release_date'].max().date(),
                className="w-100"
            )
        ], width=10),
        dbc.Col([
            html.H5("Actions", className="text-light"),
            dbc.Button("Clear Selections", id="clear-button",
                       color="primary", className="w-100")
        ], width=2, className="align-self-end")
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='genre-radial-graph'), width=4),
        dbc.Col(dcc.Graph(id='top-genres-votes-graph'), width=4),
        dbc.Col(dcc.Graph(id='top-movies-votes-graph'), width=4)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='top-genres-score-graph'), width=6),
        dbc.Col(dcc.Graph(id='top-movies-score-graph'), width=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='director-graph'), width=6),
        dbc.Col(dcc.Graph(id='actor-graph'), width=6)
    ])
], fluid=True, className="bg-dark text-light p-4")


@app.callback(
    Output('filtered-data-store', 'data'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('genre-radial-graph', 'clickData'),
    Input('top-genres-votes-graph', 'clickData'),
    Input('top-movies-votes-graph', 'clickData'),
    Input('top-genres-score-graph', 'clickData'),
    Input('top-movies-score-graph', 'clickData'),
    Input('director-graph', 'clickData'),
    Input('actor-graph', 'clickData'),
    Input('clear-button', 'n_clicks')
)
def update_filtered_data_store(start_date, end_date,
                               radial_click, genre_vote_click, movie_vote_click,
                               genre_score_click, movie_score_click,
                               director_click, actor_click, clear_clicks):

    triggered = ctx.triggered_id
    if triggered == 'clear-button':
        return df.index.tolist()

    filtered = df.copy()
    if start_date and end_date:
        mask = (
            (filtered['release_date'] >= start_date) &
            (filtered['release_date'] <= end_date)
        )
        filtered = filtered[mask]

    if triggered == 'genre-radial-graph' and radial_click:
        genre = radial_click['points'][0]['theta']
        ids = df_exploded.loc[df_exploded['genre_list'] == genre, 'movieId']
        filtered = filtered[filtered['movieId'].isin(ids)]

    if triggered == 'top-genres-votes-graph' and genre_vote_click:
        genre = genre_vote_click['points'][0]['y']
        ids = df_exploded.loc[df_exploded['genre_list'] == genre, 'movieId']
        filtered = filtered[filtered['movieId'].isin(ids)]

    if triggered == 'top-genres-score-graph' and genre_score_click:
        genre = genre_score_click['points'][0]['y']
        ids = df_exploded.loc[df_exploded['genre_list'] == genre, 'movieId']
        filtered = filtered[filtered['movieId'].isin(ids)]

    if triggered in ('top-movies-votes-graph','top-movies-score-graph'):
        click = movie_vote_click or movie_score_click
        if click:
            title = click['points'][0]['y']
            filtered = filtered[filtered['title'] == title]

    if triggered == 'director-graph' and director_click:
        name = director_click['points'][0]['y']
        filtered = filtered[filtered['director'] == name]

    if triggered == 'actor-graph' and actor_click:
        name = actor_click['points'][0]['y']
        filtered = filtered[filtered['lead_actor'] == name]

    return filtered.index.tolist()


def create_update_graph_callback(graph_id):

    @app.callback(
        Output(graph_id, 'figure'),
        Input('filtered-data-store', 'data')
    )
    def update_graph(filtered_idx):
        def empty_fig(msg="No Data Available"):
            fig = go.Figure()
            fig.update_layout(
                template=plotly_template,
                title_text=graph_titles[graph_id],
                title_x=0.5,
                xaxis={'visible': False},
                yaxis={'visible': False},
                annotations=[{
                    'text': msg,
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 16, 'color': 'gray'}
                }]
            )
            return fig

        if not filtered_idx:
            return empty_fig("Apply a filter to see data")

        sub = df.loc[filtered_idx]
        if sub.empty:
            return empty_fig()

        sub_ex = df_exploded[df_exploded['movieId'].isin(sub['movieId'])]

        if graph_id == 'genre-radial-graph':
            counts = sub_ex['genre_list'].value_counts().reset_index()
            if counts.empty:
                return empty_fig()
            fig = go.Figure(go.Barpolar(
                r=counts['genre_list'],
                theta=counts['index'],
                marker_color=px.colors.qualitative.Plotly
            ))

        elif graph_id == 'top-genres-votes-graph':
            agg = get_grouped_aggregated_data(
                sub_ex, 'genre_list', {'vote_average':'mean'}
            )
            top5 = agg.nlargest(5, 'vote_average').sort_values('vote_average')
            if top5.empty:
                return empty_fig()
            fig = go.Figure(go.Bar(
                x=top5['vote_average'],
                y=top5['genre_list'],
                orientation='h'
            ))

        elif graph_id == 'top-movies-votes-graph':
            top5 = get_top_n_values(sub, 'title', n=5, by_column='vote_count')
            top5 = top5.sort_values('vote_count')
            if top5.empty:
                return empty_fig()
            fig = go.Figure(go.Bar(
                x=top5['vote_count'],
                y=top5['title'],
                orientation='h'
            ))

        elif graph_id == 'top-genres-score-graph':
            agg = get_grouped_aggregated_data(
                sub_ex, 'genre_list', {'movieId':'count'}
            ).rename(columns={'movieId':'movie_count'})
            top10 = agg.nlargest(10, 'movie_count').sort_values('movie_count')
            if top10.empty:
                return empty_fig()
            fig = go.Figure(go.Bar(
                x=top10['movie_count'],
                y=top10['genre_list'],
                orientation='h'
            ))

        elif graph_id == 'top-movies-score-graph':
            top10 = get_top_n_values(sub, 'title', n=10, by_column='score')
            top10 = top10.sort_values('score')
            if top10.empty:
                return empty_fig()
            fig = go.Figure(go.Bar(
                x=top10['score'],
                y=top10['title'],
                orientation='h'
            ))

        elif graph_id == 'director-graph':
            agg = get_grouped_aggregated_data(
                sub.dropna(subset=['director']),
                'director',
                {'score':'mean','movieId':'count'}
            )
            top10 = agg.nlargest(10, 'score').sort_values('score')
            if top10.empty:
                return empty_fig()
            fig = go.Figure(go.Bar(
                x=top10['score'],
                y=top10['director'],
                orientation='h',
                customdata=top10['movieId'],
                hovertemplate='<b>%{y}</b><br>Avg. Score: %{x:.2f}<br>Movies: %{customdata}<extra></extra>'
            ))

        else:  # actor-graph
            agg = get_grouped_aggregated_data(
                sub.dropna(subset=['lead_actor']),
                'lead_actor',
                {'score':'mean','movieId':'count'}
            )
            top10 = agg.nlargest(10, 'score').sort_values('score')
            if top10.empty:
                return empty_fig()
            fig = go.Figure(go.Bar(
                x=top10['score'],
                y=top10['lead_actor'],
                orientation='h',
                customdata=top10['movieId'],
                hovertemplate='<b>%{y}</b><br>Avg. Score: %{x:.2f}<br>Movies: %{customdata}<extra></extra>'
            ))

        fig.update_layout(
            template=plotly_template,
            title_text=graph_titles[graph_id],
            title_x=0.5,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    return update_graph

for gid in graph_titles:
    globals()[f'update_{gid.replace("-", "_")}'] = create_update_graph_callback(gid)

if __name__ == '__main__':
    app.run_server(debug=True)
