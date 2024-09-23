import numpy as np
import pandas as pd


def load_data(file_path):
    """
    Load data from the specified CSV file.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pandas.DataFrame: The loaded data as a pandas DataFrame.
    """
    return pd.read_csv(file_path)

def preprocess_data(df):
    """
    Preprocess the input dataframe.

    Args:
        df (pandas.DataFrame): The input dataframe to be preprocessed.

    Returns:
        pandas.DataFrame: The preprocessed dataframe.
    """
    dfz = convert_cols_zero_one(df)
    df_prep = prep_dataset(dfz)
    return df_prep

def convert_cols_zero_one(df):
    """
    Converts categorical columns to binary (0/1) format for network analysis.

    Args:
        df (pandas.DataFrame): The input DataFrame to be converted.

    Returns:
        pandas.DataFrame: The DataFrame with applicable columns converted to binary format.
    """
    for var in df:
        if (df[var].nunique()) == 1:
            cell_text = df[var].dropna().unique()[0]
            df[var] = df[var].replace(cell_text, 1)
            df[var].fillna(0, inplace=True)
    return df

def prep_dataset(df, nodes=None):
    """
    Prepare the dataset for network analysis by grouping and merging data.

    Args:
        df (pandas.DataFrame): The input DataFrame to be prepared.
        nodes (list, optional): A list of column names to include in the output.

    Returns:
        pandas.DataFrame: The prepared DataFrame.
    """
    df_grouped = df.groupby(["Refid"]).max()
    df_grouped_cat = df.groupby(["Refid"])[
        "LifeStage", "Chemical", "Reference Type"
    ].agg(pd.Series.mode)
    df_grouped = df_grouped.merge(
        df_grouped_cat, left_index=True, right_index=True
    ).reset_index()

    if nodes is None:
        return df_grouped
    df_nodes = df_grouped[nodes]
    return df_nodes

def apply_filters(df, selected_filters):
    """
    Apply filters to the input dataframe based on selected filters.

    Args:
        df (pandas.DataFrame): The input dataframe to be filtered.
        selected_filters (dict): A dictionary of filters to be applied to the dataframe.

    Returns:
        pandas.DataFrame: The filtered dataframe.
    """
    return filter_all(df, multilabel=[selected_filters])

def filter_and_or(df, tag_filter, operator="and", return_mask=False):
    """
    Filter a DataFrame based on specified tags using 'and' or 'or' logic.

    Args:
        df (pandas.DataFrame): The input DataFrame to be filtered.
        tag_filter (list): A list of column names to use as filters.
        operator (str, optional): The logical operator to use when combining filters.
        return_mask (bool, optional): If True, returns the boolean mask instead of
            the filtered DataFrame.

    Returns:
        pandas.DataFrame or numpy.ndarray: The filtered DataFrame if return_mask is False,
        otherwise a boolean mask indicating which rows passed the filter.
    """
    if not tag_filter:
        df_filter = df
        filter_mask = [True] * df.shape[0]
    else:
        filter_rows = df[tag_filter].to_numpy()
        if operator == "and":
            filter_mask = np.logical_and.reduce(filter_rows, axis=1)
        else:
            filter_mask = np.logical_or.reduce(filter_rows, axis=1)
        df_filter = df[filter_mask]

    if return_mask is True:
        return filter_mask
    return df_filter

def filter_all(df, multilabel=None, multiclass=None):
    """
    Apply multiple filters to a DataFrame based on multilabel and multiclass criteria.

    Args:
        df (pandas.DataFrame): The input DataFrame to be filtered.
        multilabel (list of lists, optional): A list of lists, where each inner list contains column names to be combined with OR logic.
        multiclass (list of dicts, optional): A list of dictionaries, each containing 'name' (column name) and 'categories' (list of categories to include).

    Returns:
        pandas.DataFrame: The filtered DataFrame.
    """
    if multiclass:
        for var in multiclass:
            if var["categories"]:
                df = df.loc[df[var["name"]].isin(var["categories"])]

    if multilabel:
        filters = tuple(filter_and_or(df, list(var), "or", True) for var in multilabel)
        filter_rows = np.c_[filters]

        filter_mask = np.logical_and.reduce(filter_rows, axis=1)
        return df[filter_mask]
    return df

def create_edge_color_map(color_file_path):
    """
    Create a color map for edges in a network graph.

    Args:
        color_file_path (str): Path to the CSV file containing edge color information.

    Returns:
        dict: A nested dictionary where the outer keys are entity_1, the inner keys
        are entity_2, and the values are dictionaries containing 'color' and 'label'
        for each edge. The map includes both directions for undirected graphs.
    """
    edges = pd.read_csv(color_file_path)
    edge_color_map = {}

    for _, row in edges.iterrows():
        entity_1 = row["entity_1"]
        entity_2 = row["entity_2"]
        color = row["edge_color"]
        label = row["edge_label"]

        if entity_1 not in edge_color_map:
            edge_color_map[entity_1] = {}
        edge_color_map[entity_1][entity_2] = {"color": color, "label": label}

        # Add reverse direction for undirected graph
        if entity_2 not in edge_color_map:
            edge_color_map[entity_2] = {}
        edge_color_map[entity_2][entity_1] = {"color": color, "label": label}

    return edge_color_map

def get_edge_color(edge_color_map, node1, node2):
    """
    Get the color of an edge between two nodes.

    Args:
        edge_color_map (dict): A dictionary mapping node pairs to edge colors.
        node1 (str): The first node of the edge.
        node2 (str): The second node of the edge.

    Returns:
        str: The color of the edge if found in the map, otherwise 'lightgrey'.
    """
    if node1 in edge_color_map and node2 in edge_color_map[node1]:
        return edge_color_map[node1][node2]["color"]
    return "lightgrey"
