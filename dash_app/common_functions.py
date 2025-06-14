# import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# from typing import List, Dict, Any, Union, Tuple


# def get_column(df: pd.DataFrame, column: str) -> np.ndarray:
#     return df[column].values

# def get_column_unique_values(df: pd.DataFrame, column: str) -> pd.Series:
#     df = df[column].dropna().unique()
#     return sorted(df)


# def get_column_value_counts(df: pd.DataFrame, column: str, normalize: bool = False) -> pd.Series:
#     return df[column].value_counts(normalize=normalize)


# def get_rows_by_value(df: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
#     return df[df[column] == value]


# def get_grouped_mean(df: pd.DataFrame, group_by_column: str, target_column: str) -> pd.Series:
#     return df.groupby(group_by_column)[target_column].mean()


# def get_grouped_sum(df: pd.DataFrame, group_by_column: str, target_column: str) -> pd.Series:
#     return df.groupby(group_by_column)[target_column].sum()


# def get_column_min_max(df: pd.DataFrame, column: str) -> Dict[str, Any]:
#     if pd.api.types.is_numeric_dtype(df[column]):
#         return {"min_value": df[column].min(), "max_value": df[column].max()}
#     return {"min_value": None, "max_value": None}


# def get_column_percentiles(df: pd.DataFrame, column: str, percentiles: List[float]) -> pd.Series:
#     if pd.api.types.is_numeric_dtype(df[column]):
#         return df[column].quantile(percentiles)
#     return pd.Series(dtype=float)


# def get_grouped_aggregated_data(
#     df: pd.DataFrame,
#     group_by_columns: Union[str, List[str]],
#     aggregations: Dict[str, Union[str, Tuple[str, str]]]
# ) -> pd.DataFrame:
#     if isinstance(group_by_columns, str):
#         group_by_columns = [group_by_columns]
#     return df.groupby(group_by_columns, dropna=False).agg(**aggregations).reset_index()


# def get_filtered_and_aggregated_data(df: pd.DataFrame,
#                                      filter_column: str,
#                                      filter_values: List[Any],
#                                      group_by_column: str,
#                                      target_column: str,
#                                      agg_func: str = 'sum') -> pd.Series:
#     filtered_df = df[df[filter_column].isin(filter_values)]

#     if filtered_df.empty:
#         print(f"No data found for {filter_column} in {filter_values}.")
#         return pd.Series(dtype=float)
#     if agg_func == 'sum':
#         return filtered_df.groupby(group_by_column)[target_column].sum()
#     elif agg_func == 'mean':
#         return filtered_df.groupby(group_by_column)[target_column].mean()
#     elif agg_func == 'count':
#         return filtered_df.groupby(group_by_column)[target_column].count()
#     else:
#         raise ValueError("agg_func must be 'sum', 'mean', or 'count'")

# def get_distribution_data(df: pd.DataFrame, column: str, bins: Union[int, List[Union[int, float]]] = 10) -> pd.DataFrame:
#     if not pd.api.types.is_numeric_dtype(df[column]):
#         return pd.DataFrame()
#     counts, bin_edges = np.histogram(df[column].dropna(), bins=bins)
#     return pd.DataFrame({
#         'bin_start': bin_edges[:-1],
#         'bin_end': bin_edges[1:],
#         'count': counts
#     })



# def get_correlation_matrix(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
#     numeric_df = df[columns].select_dtypes(include=np.number)
#     if numeric_df.empty:
#         print("Warning: No numeric columns found among the specified list for correlation.")
#         return pd.DataFrame()
#     return numeric_df.corr()


# def get_time_series_data(df: pd.DataFrame, date_column: str, value_column: str, agg_func: str = 'sum', freq: str = 'M') -> pd.DataFrame:

#     df_copy = df.copy()
#     df_copy[date_column] = pd.to_datetime(df_copy[date_column])
#     df_copy = df_copy.set_index(date_column)

#     if agg_func == 'sum':
#         return df_copy[value_column].resample(freq).sum().reset_index()
#     elif agg_func == 'mean':
#         return df_copy[value_column].resample(freq).mean().reset_index()
#     elif agg_func == 'count':
#         return df_copy[value_column].resample(freq).count().reset_index()
#     else:
#         raise ValueError("agg_func must be 'sum', 'mean', or 'count'")

# def get_top_n_values(df: pd.DataFrame, column: str, n: int = 10, by_column: str = None) -> pd.DataFrame:

#     if by_column:
#         return df.groupby(column)[by_column].sum().nlargest(n).reset_index()
#     else:
#         return df[column].value_counts().nlargest(n).reset_index(name='count')
    

# def create_scatter_matrix(
#     df: pd.DataFrame,
#     numerical_columns: List[str],
#     color_column: str | None = None,
#     title: str = "Scatter Matrix",
#     hover_data: List[str] | None = None,
# ) -> go.Figure:
#     df_plot = df[numerical_columns + ([color_column] if color_column else []) + (hover_data or [])].copy()
#     numeric_only_cols = [col for col in numerical_columns if pd.api.types.is_numeric_dtype(df_plot[col])]
#     if not numeric_only_cols:
#         return go.Figure()
#     num_cols = len(numeric_only_cols)
#     fig = make_subplots(rows=num_cols, cols=num_cols, shared_xaxes=False, shared_yaxes=False,
#                         vertical_spacing=0.05, horizontal_spacing=0.05)
#     if hover_data:
#         custom_data_values = df_plot[hover_data].values
#         hovertemplate_extra = "".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data)])
#     else:
#         custom_data_values = None
#         hovertemplate_extra = ""
#     for i in range(num_cols):
#         for j in range(num_cols):
#             row_idx, col_idx = i + 1, j + 1
#             if i == j:
#                 fig.add_trace(
#                     go.Histogram(
#                         x=df_plot[numeric_only_cols[i]],
#                         name=numeric_only_cols[i],
#                         marker_color="#1f77b4",
#                         hovertemplate=f"<b>{numeric_only_cols[i]}:</b> %{{x}}<br><b>Count:</b> %{{y}}<extra></extra>",
#                     ),
#                     row=row_idx,
#                     col=col_idx,
#                 )
#                 fig.update_xaxes(title_text=numeric_only_cols[i], row=row_idx, col=col_idx)
#                 fig.update_yaxes(title_text="Count", row=row_idx, col=col_idx)
#             else:
#                 colors = None
#                 if color_column and color_column in df_plot.columns:
#                     unique_colors = df_plot[color_column].unique()
#                     color_map = {val: f"hsl({np.random.randint(0, 360)}, 50%, 50%)" for val in unique_colors}
#                     colors = df_plot[color_column].map(color_map)
#                 fig.add_trace(
#                     go.Scattergl(
#                         x=df_plot[numeric_only_cols[j]],
#                         y=df_plot[numeric_only_cols[i]],
#                         mode="markers",
#                         marker=dict(size=5, opacity=0.6, color=colors, line=dict(width=0.5, color="DarkSlateGrey")),
#                         name=f"{numeric_only_cols[i]} vs {numeric_only_cols[j]}",
#                         hovertemplate=(
#                             f"<b>{numeric_only_cols[j]}:</b> %{{x}}<br>"
#                             f"<b>{numeric_only_cols[i]}:</b> %{{y}}" +
#                             (f"<br><b>{color_column}:</b> %{{marker.color}}" if color_column else "") +
#                             hovertemplate_extra +
#                             "<extra></extra>",
#                         ),
#                         customdata=custom_data_values,
#                     ),
#                     row=row_idx,
#                     col=col_idx,
#                 )
#                 fig.update_xaxes(title_text=numeric_only_cols[j], row=row_idx, col=col_idx)
#                 fig.update_yaxes(title_text=numeric_only_cols[i], row=row_idx, col=col_idx)
#     fig.update_layout(
#         title_text=f"<b>{title}</b>",
#         height=num_cols * 300,
#         width=num_cols * 300,
#         showlegend=True,
#         template="plotly_white",
#         font=dict(family="Arial", size=10, color="#7f7f7f"),
#         title_x=0.5,
#         hovermode="closest",
#     )
#     return fig


# def create_bar_chart(
#     df: pd.DataFrame,
#     x_column: str,
#     y_column: str,
#     title: str = "Bar Chart",
#     x_axis_title: str = "",
#     y_axis_title: str = "",
#     color_column: str = None,
#     hover_data: List[str] = None,
#     sort_by_y: bool = False
# ) -> go.Figure:
#     df_plot = df.copy()
#     if sort_by_y:
#         df_plot = df_plot.sort_values(by=y_column, ascending=False)

#     data = []
#     if color_column:
#         for val in df_plot[color_column].unique():
#             subset_df = df_plot[df_plot[color_column] == val]
#             data.append(
#                 go.Bar(
#                     x=subset_df[x_column],
#                     y=subset_df[y_column],
#                     name=str(val),
#                     hovertemplate=(
#                         f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
#                         f"<b>{y_axis_title or y_column}:</b> %{{y}}" +
#                         ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
#                         "<extra></extra>"
#                     ),
#                     customdata=subset_df[hover_data].values if hover_data else None,
#                     marker_color=None
#                 )
#             )
#     else:
#         data.append(
#             go.Bar(
#                 x=df_plot[x_column],
#                 y=df_plot[y_column],
#                 marker_color="#1f77b4",
#                 hovertemplate=(
#                     f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
#                     f"<b>{y_axis_title or y_column}:</b> %{{y}}" +
#                     ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
#                     "<extra></extra>"
#                 ),
#                 customdata=df_plot[hover_data].values if hover_data else None,
#             )
#         )

#     fig = go.Figure(data=data)

#     fig.update_layout(
#         title_text=f"<b>{title}</b>",
#         xaxis_title=x_axis_title or x_column,
#         yaxis_title=y_axis_title or y_column,
#         hovermode="closest",
#         template="plotly_white",
#         bargap=0.2,
#         font=dict(family="Arial", size=12, color="#7f7f7f"),
#         title_x=0.5,
#     )
#     return fig


# def create_double_bar_chart(
#     df: pd.DataFrame,
#     x_column: str,
#     y1_column: str,
#     y2_column: str,
#     y1_name: str,
#     y2_name: str,
#     title: str = "Double Bar Chart",
#     x_axis_title: str = "",
#     y_axis_title: str = "",
#     hover_data: List[str] = None
# ) -> go.Figure:
#     fig = go.Figure([
#         go.Bar(
#             name=y1_name,
#             x=df[x_column],
#             y=df[y1_column],
#             marker_color="#636efa",
#             hovertemplate=(
#                 f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
#                 f"<b>{y1_name}:</b> %{{y}}" +
#                 ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
#                 "<extra></extra>"
#             ),
#             customdata=df[hover_data].values if hover_data else None,
#         ),
#         go.Bar(
#             name=y2_name,
#             x=df[x_column],
#             y=df[y2_column],
#             marker_color="#ef553b",
#             hovertemplate=(
#                 f"<b>{x_axis_title or x_column}:</b> %{{x}}<br>"
#                 f"<b>{y2_name}:</b> %{{y}}" +
#                 ("".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])) +
#                 "<extra></extra>"
#             ),
#             customdata=df[hover_data].values if hover_data else None,
#         )
#     ])

#     fig.update_layout(
#         barmode="group",
#         title_text=f"<b>{title}</b>",
#         xaxis_title=x_axis_title or x_column,
#         yaxis_title=y_axis_title or f"{y1_name} / {y2_name}",
#         hovermode="closest",
#         template="plotly_white",
#         font=dict(family="Arial", size=12, color="#7f7f7f"),
#         title_x=0.5,
#         legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.8)")
#     )
#     return fig


# def create_time_series_plot(
#     df: pd.DataFrame,
#     date_column: str,
#     value_column: str,
#     title: str = "Time Series Plot",
#     x_axis_title: str = "Date",
#     y_axis_title: str = "",
#     line_name: str = "Value",
#     hover_data: List[str] = None
# ) -> go.Figure:
#     df_plot = df.copy()
#     df_plot[date_column] = pd.to_datetime(df_plot[date_column])
#     df_plot = df_plot.sort_values(by=date_column)

#     hovertemplate_base = (
#         f"<b>{x_axis_title or date_column}:</b> %{{x|%Y-%m-%d}}<br>"
#         f"<b>{y_axis_title or line_name}:</b> %{{y}}"
#     )
#     hovertemplate_extra = "".join([f"<br><b>{col}:</b> %{{customdata[{i}]}}" for i, col in enumerate(hover_data or [])])
#     hovertemplate = hovertemplate_base + hovertemplate_extra + "<extra></extra>"

#     fig = go.Figure([
#         go.Scatter(
#             x=df_plot[date_column],
#             y=df_plot[value_column],
#             mode="lines+markers",
#             name=line_name,
#             line=dict(color="#1f77b4", width=2),
#             marker=dict(size=6, opacity=0.8),
#             hovertemplate=hovertemplate,
#             customdata=df_plot[hover_data].values if hover_data else None,
#         )
#     ])

#     fig.update_layout(
#         title_text=f"<b>{title}</b>",
#         xaxis_title=x_axis_title,
#         yaxis_title=y_axis_title or value_column,
#         hovermode="x unified",
#         template="plotly_white",
#         font=dict(family="Arial", size=12, color="#7f7f7f"),
#         title_x=0.5,
#         xaxis=dict(
#             rangeslider_visible=True,
#             rangeselector=dict(
#                 buttons=[
#                     dict(count=1, label="1m", step="month", stepmode="backward"),
#                     dict(count=6, label="6m", step="month", stepmode="backward"),
#                     dict(count=1, label="YTD", step="year", stepmode="todate"),
#                     dict(count=1, label="1y", step="year", stepmode="backward"),
#                     dict(step="all")
#                 ]
#             )
#         )
#     )
#     return fig


# def create_radial_chart(
#     df: pd.DataFrame,
#     categories_column: str,
#     values_column: str,
#     group_column: str,
#     title: str = "Radial Chart",
#     range_min: float = None,
#     range_max: float = None
# ) -> go.Figure:
#     fig = go.Figure()
#     all_categories = df[categories_column].unique()
#     categories_ordered = sorted(all_categories)

#     for group_val in df[group_column].unique():
#         subset_df = df[df[group_column] == group_val].copy()
#         subset_df = subset_df.set_index(categories_column).reindex(categories_ordered, fill_value=0).reset_index()
#         hovertemplate = (
#             f"<b>{group_column}:</b> {group_val}<br>"
#             f"<b>{categories_column}:</b> %{{theta}}<br>"
#             f"<b>{values_column}:</b> %{{r}}<extra></extra>"
#         )
#         fig.add_trace(go.Scatterpolar(
#             r=subset_df[values_column],
#             theta=subset_df[categories_column],
#             fill="toself",
#             name=str(group_val),
#             hovertemplate=hovertemplate
#         ))

#     min_val = df[values_column].min() if range_min is None else range_min
#     max_val = df[values_column].max() if range_max is None else range_max
#     if range_min is None:
#         min_val *= 0.9
#     if range_max is None:
#         max_val *= 1.1

#     fig.update_layout(
#         polar=dict(
#             radialaxis=dict(
#                 visible=True,
#                 range=[min_val, max_val],
#                 showline=False,
#                 tickfont_size=10,
#                 linecolor="#d3d3d3"
#             ),
#             angularaxis=dict(
#                 tickfont_size=12,
#                 rotation=90,
#                 direction="clockwise",
#                 linecolor="#d3d3d3"
#             ),
#             bgcolor="rgba(0,0,0,0)"
#         ),
#         title_text=f"<b>{title}</b>",
#         hovermode="closest",
#         template="plotly_white",
#         font=dict(family="Arial", size=12, color="#7f7f7f"),
#         title_x=0.5,
#         legend=dict(x=1.05, y=1, bgcolor="rgba(255,255,255,0.8)")
#     )
#     return fig


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Union, Tuple


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
    
    # =================================================================================
    # FIX: Pass the 'aggregations' dictionary directly to .agg().
    # The ** unpacking is incorrect for this type of aggregation in modern pandas.
    return df.groupby(group_by_columns, dropna=False).agg(aggregations).reset_index()
    # =================================================================================


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