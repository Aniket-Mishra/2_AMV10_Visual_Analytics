import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Union, Tuple


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
    return df.groupby(group_by_column)[target_column].mean()


def get_grouped_sum(df: pd.DataFrame, group_by_column: str, target_column: str) -> pd.Series:
    return df.groupby(group_by_column)[target_column].sum()


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
        return filtered_df.groupby(group_by_column)[target_column].sum()
    elif agg_func == 'mean':
        return filtered_df.groupby(group_by_column)[target_column].mean()
    elif agg_func == 'count':
        return filtered_df.groupby(group_by_column)[target_column].count()
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