import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Union, Tuple
import plotly.express as px
import plotly.graph_objects as go

# A function to return all the unique values on a given column
#
# @param df - pandas dataframe
# @param column - column to get unique values from
# @returns sorted series containing all the unique values from a given column and dataframe
def get_column_unique_values(df: pd.DataFrame, column: str) -> pd.Series:
    df = df[column].dropna().unique()
    return sorted(df)

# A function to get the mean of every entry in a group for a given target value
#
# @param df - pandas dataframe
# @param group_by_column - the column to group by and get the mean of
# @param target_column - the value to get the mean of
# @returns series containg the mean value for each entry of a given column
def get_grouped_mean(df: pd.DataFrame, group_by_column: str, target_column: str) -> pd.Series:
    return df.groupby(group_by_column, observed=True)[target_column].mean()

# Get the movie pool of a filtered dataframe using selected genres, years and directors
#
# @param filtered_df - pandas dataframe that is already (partially) prefiltered
# @param genre_ids - genres to filter on
# @param year_range - years to filter on
# @param director_ids - directors to filter on
# @returns filtered pool of movies
def get_movie_pool(filtered_df, genre_ids=None, year_range=None, director_ids=None):
    df = filtered_df
    if genre_ids is not None:
        df = df[df['main_genre_id'].isin(genre_ids)]
    if year_range is not None:
        df = df[(df['release_year'] >= year_range[0]) & (df['release_year'] <= year_range[1])]
    if director_ids is not None:
        df = df[df['director_id'].isin(director_ids)]
    return df

# Recommends a top n movie for a given user, using the clustered data
#
# @param user_id - the id of the user to give the recommendation for
# @param filtered_df - pandas dataframe of movies
# @param df_ratings - pandas dataframe of user ratings
# @param df_users - pandas dataframe of user information and stats
# @param n_recs - top n recommendations to return
# @param explain - enable explanation why a certain movie has been recommended
# @param overview_topic_cols - columns in the overview
# @param topic_words - all topic words in overview
# @param tag_topic_cols - columns in the tags
# @param tag_topic_words - all topic words in tags
# @returns top n recommendations. fully if explain=True, movieID and title if explain=False
def recommend_movies_for_user(
    user_id,
    filtered_df,
    df_ratings,
    df_users,
    n_recs=5,
    explain=True,
    overview_topic_cols=None,
    topic_words=None,
    tag_topic_cols=None,
    tag_topic_words=None,
):
    seen = df_ratings[df_ratings['userId'] == user_id]['movieId'].tolist()
    pool = filtered_df[~filtered_df['movieId'].isin(seen)].copy()
    if pool.empty:
        return []

    user_row = df_users[df_users['userId'] == user_id]
    user_top_genres = [user_row['top_genre_1_id'].values[0], user_row['top_genre_2_id'].values[0]]

    pool['score'] = 0
    pool.loc[pool['main_genre_id'].isin(user_top_genres), 'score'] += 1
    if 'movie_cluster' in pool.columns and 'user_cluster' in user_row.columns:
        pool.loc[pool['movie_cluster'] == user_row['user_cluster'].values[0], 'score'] += 1
    pool['score'] += pool['popularity_score'].rank(pct=True)
    pool['score'] += pool['critical_success'].rank(pct=True)
    pool['score'] += pool['vote_average'].rank(pct=True)

    pool = pool.sort_values('score', ascending=False)
    recs = pool.head(n_recs)

    explanations = []
    for _, row in recs.iterrows():
        why = []
        if row['main_genre_id'] in user_top_genres:
            why.append(f"Matches your favorite genre ({row['main_genre']})")
        if 'movie_cluster' in pool.columns and row['movie_cluster'] == user_row['user_cluster'].values[0]:
            why.append(f"In your preferred cluster (based on similar movies)")
        if row['popularity_score'] > pool['popularity_score'].median():
            why.append("Popular among other users")
        if row['critical_success'] > pool['critical_success'].median():
            why.append("Critically acclaimed")
        # Top topics/keywords/themes
        topic_strs = []
        if overview_topic_cols is not None and topic_words is not None:
            theme_words = get_top_topic_words(row, overview_topic_cols, topic_words, n=2)
            if theme_words:
                topic_strs.append("Overview: " + theme_words)
        else:
            print(overview_topic_cols)
        if tag_topic_cols is not None and tag_topic_words is not None:
            tag_words = get_top_topic_words(row, tag_topic_cols, tag_topic_words, n=2)
            if tag_words:
                topic_strs.append("Tags: " + tag_words)
        else:
            print(tag_topic_cols)
        if topic_strs:
            why.append("Notable themes: " + " | ".join(topic_strs))
        explanations.append({
            "movieId": row['movieId'],
            "title": row['title'],
            "explanation": "; ".join(why)
        })

    if explain:
        return explanations
    else:
        return recs[['movieId', 'title']]

# Return the most salient topics/words for this row.
#
# @param row - row to get topics/words from
# @param topic_cols - the topic columns
# @param topic_words - the topic words
# @param n - top n indices
# @returns most salient topics
def get_top_topic_words(row, topic_cols, topic_words, n=2):
    # Get the topic indices sorted by strength
    topic_strengths = [(i, row[topic_col]) for i, topic_col in enumerate(topic_cols)]
    topic_strengths.sort(key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, _ in topic_strengths[:n]]
    words = []
    for idx in top_indices:
        words.extend(topic_words.get(idx, []))
    return ', '.join(words[:8])

# Create a special dataframe used for recommendation plots
# Specifically for the watched data of a user
#
# @param df_ratings - pandas dataframe of user ratings
# @param df_filtered - filtered pandas dataframe
# @param user_id - the id of the user to create the plot on (their watched data)
# @param filtered_pool - filtered pool of movies
# @param recs - recommendations for the gives user id
# @param special dataframe tailered for create_recommended_scatter_plot and create_bar_recs_plot
def get_plot_df(
        df_ratings: pd.DataFrame,
        df_filtered: pd.DataFrame,
        user_id: int,
        filtered_pool,
        recs
):
    watched = df_ratings[df_ratings['userId'] == user_id][['movieId', 'rating']]
    watched = watched.loc[watched["movieId"].isin(df_filtered["movieId"])]
    watched = watched.merge(filtered_pool[['movieId', 'title', 'main_genre', 'pca_1', 'pca_2', 'movie_cluster']], on='movieId', how='inner')
    watched['status'] = 'Watched'

    recommended_ids = [rec['movieId'] for rec in recs]
    recommended = filtered_pool[filtered_pool['movieId'].isin(recommended_ids)].copy()
    recommended['status'] = 'Recommended'
    recommended['rating'] = recommended["vote_average"].values

    plot_df = pd.concat([watched, recommended], ignore_index=True)


    plot_df = pd.concat([watched, recommended], ignore_index=True)
    # Optionally, add a new column for easier color/symbol mapping
    plot_df['status'] = plot_df['status'].astype(str)

    PLOT_COLUMNS = [
        'movieId', 'title', 'main_genre', 'rating', 'status', 
        'pca_1', 'pca_2', 'movie_cluster'
    ]
    plot_df = plot_df[PLOT_COLUMNS]

    plot_columns = [
    'movieId', 'title', 'main_genre', 'rating', 'status', 
    'pca_1', 'pca_2', 'movie_cluster'
    ]

    plot_df_for_vis = plot_df[plot_columns]

    return plot_df_for_vis

# Creates a plotly bar chart
# 
# @param df - pandas dataframe
# @param x_column - column to use data for x-axis
# @param y_column - column to use data for y-axis
# @param title - title of bar chart
# @param x_axis_title - title of the x-axis
# @param y_axis_title - title of the y-axis
# @param color_column - color column
# @param hover_data - list of features to put in the hover data
# @param sort_by_y - sort value based on y-axis
# @returns plotly figure of a bar chart
def create_bar_chart(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str = "Bar Chart",
    x_axis_title: str = "",
    y_axis_title: str = "",
    color_column: str = None,
    hover_data: List[str] = None,
    sort_by_y: bool = False
) -> go.Figure:
    df_plot = df.copy()
    if sort_by_y:
        df_plot = df_plot.sort_values(by=y_column, ascending=False)

    data = []
    if color_column:
        for val in df_plot[color_column].unique():
            subset_df = df_plot[df_plot[color_column] == val]
            data.append(
                go.Bar(
                    x=subset_df[x_column],
                    y=subset_df[y_column],
                    name=str(val),
                    hovertemplate=(
                        f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
                        f"<b>{y_axis_title or y_column}:</b> %{{y}}" +
                        ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
                        "<extra></extra>"
                    ),
                    customdata=subset_df[hover_data].values if hover_data else None,
                    marker_color='#7C4DFF'
                )
            )
    else:
        data.append(
            go.Bar(
                x=df_plot[x_column],
                y=df_plot[y_column],
                marker_color="#7C4DFF",
                hovertemplate=(
                    f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
                    f"<b>{y_axis_title or y_column}:</b> %{{y}}" +
                    ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
                    "<extra></extra>"
                ),
                customdata=df_plot[hover_data].values if hover_data else None,
            )
        )

    fig = go.Figure(data=data)

    fig.update_layout(
        title_text=f"<b>{title}</b>",
        xaxis_title=x_axis_title or x_column,
        yaxis_title=y_axis_title or y_column,
        hovermode="closest",
        template="plotly_white",
        bargap=0.2,
        font=dict(family="Arial", size=12, color="#7f7f7f"),
        title_x=0.5,
    )
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )
    return fig

# Creates a plotly scatter plot, based on TSNE clusters
# 
# @param df - pandas dataframe
# @param x - column to use data for x-axis
# @param y - column to use data for y-axis
# @param color - colors to use
# @param title - title of scatter plot
# @returns plotly figure of a scatter plot
def create_cluster_scatter_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str
):
    if df.empty or x not in df or y not in df or color not in df:
        # Return empty figure if data is missing
        return go.Figure(layout=dict(
            template="plotly_dark",
            plot_bgcolor="rgba(33,33,33,1)",
            paper_bgcolor="rgba(33,33,33,1)",
            font=dict(family="Roboto, Arial", color="#FAFAFA"),
            annotations=[dict(
                text="No data to display",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=18, color="#FAFAFA")
            )]
        ))

    # Custom vibrant color palette for clusters (extend as needed)
    cluster_palette = [
        "#7C4DFF",  # Vibrant Material Purple
        "#FFD54F",  # Yellow accent for contrast
        "#00E5FF",  # Cyan
        "#FF4081",  # Pink accent
        "#FFC400",  # Amber
        "#69F0AE",  # Green accent
        "#FF5252",  # Red accent
        "#e040fb",  # Blue accent
        "#C51162",  # Deep Pink
        "#00B8D4",  # Teal
    ]

    # If you know the number of unique clusters, extend palette or repeat
    n_clusters = df[color].nunique()
    color_sequence = cluster_palette * (n_clusters // len(cluster_palette) + 1)

    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        hover_data=['title', 'main_genre', 'director', 'lead_actor', 'vote_average', 'popularity_score'],
        title=title,
        color_discrete_sequence=color_sequence[:n_clusters] if df[color].dtype == object else None,
        # For numeric columns, you can use color_continuous_scale e.g. "Turbo"
    )
    fig.update_layout(
        dragmode="select",
        template="plotly_dark",
        plot_bgcolor="rgba(33,33,33,1)",
        paper_bgcolor="rgba(33,33,33,1)",
        font=dict(family="Roboto, Arial", color="#FAFAFA"),
        legend=dict(
            bgcolor="rgba(40,40,40,0.9)",
            font=dict(color="#FAFAFA")
        ),
        title_x=0.5,
    )
    return fig

# Creates a plotly scatter plot, based on user watched and recommended movies
# 
# @param df - pandas dataframe
# @param x - column to use data for x-axis
# @param y - column to use data for y-axis
# @param color - colors to use
# @param symbol - symbol of recommended movies
# @param size - size of the symbols
# @param title - title of scatter plot
# @returns plotly figure of a scatter plot
def create_recommended_scatter_plot(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        symbol: str,
        size: str,
        title: str
):
    # Two bright and contrasting shades of purple
    PURPLE_SEQ = ["#ffab91", "#4a148c"]

    fig = px.scatter(
        df,
        x=x, 
        y=y,
        color=color,
        symbol=symbol,
        size=size,
        hover_data=['title', 'main_genre', 'rating', 'movie_cluster'],
        title=title,
        color_discrete_sequence=PURPLE_SEQ  # Use two strong purples
    )
    fig.update_layout(
        dragmode="select",
        template="plotly_dark",
        plot_bgcolor="rgba(33,33,33,1)",
        paper_bgcolor="rgba(33,33,33,1)",
        font=dict(family="Roboto, Arial", color="#FAFAFA"),
        title_x=0.5,
        legend=dict(
            bgcolor="rgba(40,40,40,0.9)",
            font=dict(color="#FAFAFA")
        ),
    )
    return fig

# Creates a plotly stacked double bar chart
# 
# @param df - pandas dataframe
# @param x - column to use data for x-axis
# @param y - column to use data for y-axis
# @param color - colors to use
# @param title - title of box chart
# @returns plotly figure of a box chart
def create_bar_recs_plot(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        title: str
):
    bar_df = df.copy()
    bar_df['User Rated'] = bar_df['status'] == 'Watched'

    fig = px.bar(
        bar_df,
        x=x, 
        y=y, 
        color=color,
        barmode='group',
        title=title,
        color_discrete_sequence=["#7e57c2", "#ffab91"]
    )
    fig.update_layout(
        dragmode="select",
        template="plotly_dark",
        plot_bgcolor="rgba(33,33,33,1)",
        paper_bgcolor="rgba(33,33,33,1)",
        font=dict(family="Roboto, Arial", color="#FAFAFA"),
        title_x=0.5,
        legend=dict(
            bgcolor="rgba(40,40,40,0.9)",
            font=dict(color="#FAFAFA")
        ),
    )
    return fig

# Creates a dynamic plotly treemap
# 
# @param df - pandas dataframe
# @param column - column to group by
# @param title - title of treemap
# @returns plotly figure of a treemap
def create_dynamic_treemap(df: pd.DataFrame, column: str, title: str = None):
    PURPLE_GRADIENT = ["#E1BEE7", "#B388FF", "#7C4DFF", "#651FFF", "#512DA8"]
    # Value counts (ignoring missing values)
    counts = df[column].value_counts(dropna=True).reset_index()
    counts.columns = [column, "count"]
    
    fig = px.treemap(
        counts,
        path=[column],
        values="count",
        color="count",
        color_continuous_scale=PURPLE_GRADIENT,
        title=title or f"Number of Movies by {column.replace('_', ' ').title()}"
    )
    fig.update_traces(textinfo="label+value")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )
    return fig

# Creates a dynamic plotly radial chart
# 
# @param df - pandas dataframe
# @param category_col - column name of the category
# @param value_col - column name for the values
# @param agg_func - the function to aggregate the values on
# @param title - title of treemap
# @param showlegend - enables the legend
# @param fill - fill to self
# @param color - color to use
# @param group_col - colum of the groups
# @param range_min - minimum range
# @param range_max - maximum range
# @param selected_catergories - categories to display in the chart
# @returns plotly figure of a radial chart
def create_dynamic_radial_chart(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    agg_func: str = "mean",
    title: str = "Radial Chart",
    showlegend: bool = False,
    fill: str = "toself",
    color: str = "#1976d2",
    group_col: str = None,
    range_min: float = None,
    range_max: float = None,
    selected_categories: list = None
) -> 'go.Figure':
    import plotly.graph_objs as go

    fig = go.Figure()
    agg_map = {
        "mean": "mean",
        "sum": "sum",
        "median": "median",
        "max": "max",
        "min": "min",
        "count": "count"
    }
    if agg_func not in agg_map:
        raise ValueError(f"agg_func must be one of {list(agg_map.keys())}")

    if group_col is not None:
        raise NotImplementedError("Grouping not supported for mini cards yet.")

    # Aggregate and **reindex to ensure exactly selected_categories, fill missing with 0**
    if selected_categories is not None:
        # Always pad to at least 3 (dummy names if fewer than 3)
        pad = 3 - len(selected_categories)
        categories = list(selected_categories)
        if pad > 0:
            categories += [f"Other{i+1}" for i in range(pad)]

        agg_df = (
            df[df[category_col].isin(selected_categories)]
            .groupby(category_col)[value_col]
            .agg(agg_map[agg_func])
            .reindex(categories, fill_value=0)
            .reset_index()
        )
    else:
        agg_df = df.groupby(category_col)[value_col].agg(agg_map[agg_func]).reset_index()
        categories = agg_df[category_col].tolist()
        # If < 3, pad
        if len(categories) < 3:
            agg_df = agg_df.reindex(list(categories) + [f"Other{i+1}" for i in range(3-len(categories))], fill_value=0)
            agg_df = agg_df.reset_index()

    fig.add_trace(go.Scatterpolar(
        r=agg_df[value_col],
        theta=agg_df[category_col],
        fill=fill,
        name=value_col,
        line=dict(color=color)
    ))

    # Range for radial axis
    radial_min = range_min if range_min is not None else agg_df[value_col].min() * 0.9
    radial_max = range_max if range_max is not None else max(1, agg_df[value_col].max() * 1.1)

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[radial_min, radial_max]),
            angularaxis=dict(tickfont_size=11),
        ),
        showlegend=showlegend,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Arial", size=11),
        title=title,
        title_x=0.5
    )
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )

    return fig