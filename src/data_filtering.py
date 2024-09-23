import numpy as np


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
