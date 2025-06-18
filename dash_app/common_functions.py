import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Union, Tuple
import plotly.express as px
import plotly.graph_objects as go


# def read_file(file_path: str):
#     file_extension = file_path.split(".")[-1]

def get_column(df: pd.DataFrame, column: str) -> np.ndarray:
    return df[column].values

def get_column_unique_values(df: pd.DataFrame, column: str) -> pd.Series:
    df = df[column].dropna().unique()
    return sorted(df)


def get_column_value_counts(df: pd.DataFrame, column: str, normalize: bool = False) -> pd.Series:
    return df[column].value_counts(normalize=normalize)


def get_rows_by_value(df: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
    return df[df[column] == value]


def get_grouped_mean(df: pd.DataFrame, group_by_column: str, target_column: str) -> pd.Series:
    return df.groupby(group_by_column, observed=True)[target_column].mean()


def get_grouped_sum(df: pd.DataFrame, group_by_column: str, target_column: str) -> pd.Series:
    return df.groupby(group_by_column, observed=True)[target_column].sum()


def get_column_min_max(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    if pd.api.types.is_numeric_dtype(df[column]):
        return {"min_value": df[column].min(), "max_value": df[column].max()}
    return {"min_value": None, "max_value": None}


def get_column_percentiles(df: pd.DataFrame, column: str, percentiles: List[float]) -> pd.Series:
    if pd.api.types.is_numeric_dtype(df[column]):
        return df[column].quantile(percentiles)
    return pd.Series(dtype=float)


def get_grouped_aggregated_data(
    df: pd.DataFrame,
    group_by_columns: Union[str, List[str]],
    aggregations: Dict[str, Union[str, Tuple[str, str]]]
) -> pd.DataFrame:
    """
    Groups a DataFrame and applies specified aggregations.
    """
    if isinstance(group_by_columns, str):
        group_by_columns = [group_by_columns]
    
    return df.groupby(group_by_columns, dropna=False).agg(aggregations).reset_index()


def get_filtered_and_aggregated_data(df: pd.DataFrame,
                                     filter_column: str,
                                     filter_values: List[Any],
                                     group_by_column: str,
                                     target_column: str,
                                     agg_func: str = 'sum') -> pd.Series:
    filtered_df = df[df[filter_column].isin(filter_values)]

    if filtered_df.empty:
        print(f"No data found for {filter_column} in {filter_values}.")
        return pd.Series(dtype=float)
    if agg_func == 'sum':
        return filtered_df.groupby(group_by_column, observed=True)[target_column].sum()
    elif agg_func == 'mean':
        return filtered_df.groupby(group_by_column, observed=True)[target_column].mean()
    elif agg_func == 'count':
        return filtered_df.groupby(group_by_column, observed=True)[target_column].count()
    else:
        raise ValueError("agg_func must be 'sum', 'mean', or 'count'")

def get_distribution_data(df: pd.DataFrame, column: str, bins: Union[int, List[Union[int, float]]] = 10) -> pd.DataFrame:
    if not pd.api.types.is_numeric_dtype(df[column]):
        return pd.DataFrame()
    counts, bin_edges = np.histogram(df[column].dropna(), bins=bins)
    return pd.DataFrame({
        'bin_start': bin_edges[:-1],
        'bin_end': bin_edges[1:],
        'count': counts
    })



def get_correlation_matrix(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    numeric_df = df[columns].select_dtypes(include=np.number)
    if numeric_df.empty:
        print("Warning: No numeric columns found among the specified list for correlation.")
        return pd.DataFrame()
    return numeric_df.corr()


def get_time_series_data(df: pd.DataFrame, date_column: str, value_column: str, agg_func: str = 'sum', freq: str = 'M') -> pd.DataFrame:

    df_copy = df.copy()
    df_copy[date_column] = pd.to_datetime(df_copy[date_column])
    df_copy = df_copy.set_index(date_column)

    if agg_func == 'sum':
        return df_copy[value_column].resample(freq).sum().reset_index()
    elif agg_func == 'mean':
        return df_copy[value_column].resample(freq).mean().reset_index()
    elif agg_func == 'count':
        return df_copy[value_column].resample(freq).count().reset_index()
    else:
        raise ValueError("agg_func must be 'sum', 'mean', or 'count'")

def get_top_n_values(df: pd.DataFrame, column: str, n: int = 10, by_column: str = None) -> pd.DataFrame:

    if by_column:
        return df.groupby(column)[by_column].sum().nlargest(n).reset_index()
    else:
        return df[column].value_counts().nlargest(n).reset_index(name='count')

def get_movie_pool(filtered_df, genre_ids=None, year_range=None, director_ids=None):
    df = filtered_df
    if genre_ids is not None:
        df = df[df['main_genre_id'].isin(genre_ids)]
    if year_range is not None:
        df = df[(df['release_year'] >= year_range[0]) & (df['release_year'] <= year_range[1])]
    if director_ids is not None:
        df = df[df['director_id'].isin(director_ids)]
    return df

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

def get_top_topic_words(row, topic_cols, topic_words, n=2):
    """Return the most salient topics/words for this row."""
    # Get the topic indices sorted by strength
    topic_strengths = [(i, row[topic_col]) for i, topic_col in enumerate(topic_cols)]
    topic_strengths.sort(key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, _ in topic_strengths[:n]]
    words = []
    for idx in top_indices:
        words.extend(topic_words.get(idx, []))
    return ', '.join(words[:8])


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

def create_scatter_matrix(
    df: pd.DataFrame,
    numerical_columns: List[str],
    color_column: str | None = None,
    title: str = "Scatter Matrix",
    hover_data: List[str] | None = None,
) -> go.Figure:
    df_plot = df[numerical_columns + ([color_column] if color_column else []) + (hover_data or [])].copy()
    numeric_only_cols = [col for col in numerical_columns if pd.api.types.is_numeric_dtype(df_plot[col])]
    if not numeric_only_cols:
        return go.Figure()
    num_cols = len(numeric_only_cols)
    fig = make_subplots(rows=num_cols, cols=num_cols, shared_xaxes=False, shared_yaxes=False,
                        vertical_spacing=0.05, horizontal_spacing=0.05)
    if hover_data:
        custom_data_values = df_plot[hover_data].values
        hovertemplate_extra = "".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data)])
    else:
        custom_data_values = None
        hovertemplate_extra = ""

    # Color palette for cluster/labels
    palette = [
        "#B388FF", "#64FFDA", "#FF80AB", "#FFD740",
        "#40C4FF", "#69F0AE", "#FFAB40", "#FF5252"
    ]

    for i in range(num_cols):
        for j in range(num_cols):
            row_idx, col_idx = i + 1, j + 1
            if i == j:
                fig.add_trace(
                    go.Histogram(
                        x=df_plot[numeric_only_cols[i]],
                        name=numeric_only_cols[i],
                        marker_color="#B388FF",   # Use light purple for hist
                        hovertemplate=f"<b>{numeric_only_cols[i]}:</b> %{{x}}<br><b>Count:</b> %{{y}}<extra></extra>",
                    ),
                    row=row_idx,
                    col=col_idx,
                )
                fig.update_xaxes(title_text=numeric_only_cols[i], row=row_idx, col=col_idx)
                fig.update_yaxes(title_text="Count", row=row_idx, col=col_idx)
            else:
                colors = None
                if color_column and color_column in df_plot.columns:
                    unique_vals = list(df_plot[color_column].unique())
                    color_map = {val: palette[idx % len(palette)] for idx, val in enumerate(unique_vals)}
                    colors = df_plot[color_column].map(color_map)
                fig.add_trace(
                    go.Scattergl(
                        x=df_plot[numeric_only_cols[j]],
                        y=df_plot[numeric_only_cols[i]],
                        mode="markers",
                        marker=dict(size=5, opacity=0.7, color=colors, line=dict(width=0.5, color="DarkSlateGrey")),
                        name=f"{numeric_only_cols[i]} vs {numeric_only_cols[j]}",
                        hovertemplate=(
                            f"<b>{numeric_only_cols[j]}:</b> %{{x}}<br>"
                            f"<b>{numeric_only_cols[i]}:</b> %{{y}}" +
                            (f"<br><b>{color_column}:</b> %{{marker.color}}" if color_column else "") +
                            hovertemplate_extra +
                            "<extra></extra>",
                        ),
                        customdata=custom_data_values,
                    ),
                    row=row_idx,
                    col=col_idx,
                )
                fig.update_xaxes(title_text=numeric_only_cols[j], row=row_idx, col=col_idx)
                fig.update_yaxes(title_text=numeric_only_cols[i], row=row_idx, col=col_idx)
    fig.update_layout(
        title_text=f"<b>{title}</b>",
        height=num_cols * 300,
        width=num_cols * 300,
        showlegend=True,
        template="plotly_dark",
        plot_bgcolor="rgba(33,33,33,1)",
        paper_bgcolor="rgba(33,33,33,1)",
        font=dict(family="Roboto, Arial", color="#FAFAFA"),
        title_x=0.5,
        hovermode="closest",
        dragmode="select",
    )
    return fig

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


def create_double_bar_chart(
    df: pd.DataFrame,
    x_column: str,
    y1_column: str,
    y2_column: str,
    y1_name: str,
    y2_name: str,
    title: str = "Double Bar Chart",
    x_axis_title: str = "",
    y_axis_title: str = "",
    hover_data: List[str] = None
) -> go.Figure:
    fig = go.Figure([
        go.Bar(
            name=y1_name,
            x=df[x_column],
            y=df[y1_column],
            marker_color="#B388FF",  # Light, high-contrast purple
            hovertemplate=(
                f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
                f"<b>{y1_name}:</b> %{{y}}" +
                ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
                "<extra></extra>"
            ),
            customdata=df[hover_data].values if hover_data else None,
        ),
        go.Bar(
            name=y2_name,
            x=df[x_column],
            y=df[y2_column],
            marker_color="#7C4DFF",  # Slightly deeper, but still vibrant
            hovertemplate=(
                f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
                f"<b>{y2_name}:</b> %{{y}}" +
                ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
                "<extra></extra>"
            ),
            customdata=df[hover_data].values if hover_data else None,
        )
    ])
    fig.update_layout(
        barmode="group",
        title_text=f"<b>{title}</b>",
        xaxis_title=x_axis_title or x_column,
        yaxis_title=y_axis_title or f"{y1_name} / {y2_name}",
        hovermode="closest",
        template="plotly_dark",
        plot_bgcolor="rgba(33,33,33,1)",
        paper_bgcolor="rgba(33,33,33,1)",
        font=dict(family="Roboto, Arial", color="#FAFAFA"),
        title_x=0.5,
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(33,33,33,0.9)")
    )
    fig.update_layout(dragmode="select")
    return fig


def create_time_series_plot(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    title: str = "Time Series Plot",
    x_axis_title: str = "Date",
    y_axis_title: str = "",
    line_name: str = "Value",
    hover_data: List[str] = None
) -> go.Figure:
    df_plot = df.copy()
    df_plot[date_column] = pd.to_datetime(df_plot[date_column])
    df_plot = df_plot.sort_values(by=date_column)

    hovertemplate_base = (
        f"<b>{x_axis_title or date_column}:</b> %{{x|%Y-%m-%d}}<br>"
        f"<b>{y_axis_title or line_name}:</b> %{{y}}"
    )
    hovertemplate_extra = "".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])
    hovertemplate = hovertemplate_base + hovertemplate_extra + "<extra></extra>"

    fig = go.Figure([
        go.Scatter(
            x=df_plot[date_column],
            y=df_plot[value_column],
            mode="lines+markers",
            name=line_name,
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6, opacity=0.8),
            hovertemplate=hovertemplate,
            customdata=df_plot[hover_data].values if hover_data else None,
        )
    ])

    fig.update_layout(
        title_text=f"<b>{title}</b>",
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title or value_column,
        hovermode="x unified",
        template="plotly_white",
        font=dict(family="Arial", size=12, color="#7f7f7f"),
        title_x=0.5,
        xaxis=dict(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ]
            )
        )
    )
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )
    return fig


def create_radial_chart(
    df: pd.DataFrame,
    categories_column: str,
    values_column: str,
    group_column: str,
    title: str = "Radial Chart",
    range_min: float = None,
    range_max: float = None
) -> go.Figure:
    fig = go.Figure()
    all_categories = df[categories_column].unique()
    categories_ordered = sorted(all_categories)

    for group_val in df[group_column].unique():
        subset_df = df[df[group_column] == group_val].copy()
        subset_df = subset_df.set_index(categories_column).reindex(categories_ordered, fill_value=0).reset_index()
        hovertemplate = (
            f"<b>{group_column}:</b> {group_val}<br>"
            f"<b>{categories_column}:</b> %{{theta}}<br>"
            f"<b>{values_column}:</b> %{{r}}<extra></extra>"
        )
        fig.add_trace(go.Scatterpolar(
            r=subset_df[values_column],
            theta=subset_df[categories_column],
            fill="toself",
            name=str(group_val),
            hovertemplate=hovertemplate
        ))

    min_val = df[values_column].min() if range_min is None else range_min
    max_val = df[values_column].max() if range_max is None else range_max
    if range_min is None:
        min_val *= 0.9
    if range_max is None:
        max_val *= 1.1

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[min_val, max_val],
                showline=False,
                tickfont_size=10,
                linecolor="#d3d3d3"
            ),
            angularaxis=dict(
                tickfont_size=12,
                rotation=90,
                direction="clockwise",
                linecolor="#d3d3d3"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        title_text=f"<b>{title}</b>",
        hovermode="closest",
        template="plotly_white",
        font=dict(family="Arial", size=12, color="#7f7f7f"),
        title_x=0.5,
        legend=dict(x=1.05, y=1, bgcolor="rgba(255,255,255,0.8)")
    )
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )
    return fig

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

def create_recomended_scatter_plot(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        symbol: str,
        size: str,
        title: str
):
    fig = px.scatter(
        df,
        x=x, 
        y=y,
        color=color,
        symbol=symbol,
        size=size,
        hover_data=['title', 'main_genre', 'rating', 'movie_cluster'],
        title=title
    )
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )
    return fig

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
        title=title
    )
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )
    return fig

def create_dynamic_treemap(df: pd.DataFrame, column: str, title: str = None):
    """
    Creates a treemap showing the number of items per unique value in the given column.
    
    Args:
        df (pd.DataFrame): Your DataFrame.
        column (str): The column to group by (categorical).
        title (str): Title for the plot.
    
    Returns:
        plotly.graph_objs._figure.Figure
    """
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

def mini_radial_figure(genres, df):
    counts = [df[df['main_genre'] == g].shape[0] for g in genres]
    fig = go.Figure(
        data=[go.Barpolar(
            r=counts,
            theta=[g[:12] for g in genres],
            marker_color=['#1976d2', '#64b5f6', '#90caf9'],
            width=[30]*len(counts),
            opacity=0.8
        )]
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, showticklabels=False, ticks=''),
            angularaxis=dict(showticklabels=True)
        ),
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        height=110
    )
    fig.update_layout(dragmode="select")
    fig.update_layout(
    template="plotly_dark",  # instead of "plotly_white"
    plot_bgcolor="rgba(33,33,33,1)",  # match --md-bg
    paper_bgcolor="rgba(33,33,33,1)",
    font=dict(family="Roboto, Arial", color="#FAFAFA"),
    )
    return fig