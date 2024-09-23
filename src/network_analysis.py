import math

from mlxtend.frequent_patterns import apriori, association_rules
from streamlit_agraph import Config, Edge, Node, agraph

from data_processing import get_edge_color


def create_network(df_net, edge_color_map):
    """
    Create a network visualization based on the input DataFrame.

    Args:
        df_net (pandas.DataFrame): The input DataFrame containing the network data.
        edge_color_map (dict): A dictionary mapping edge pairs to their respective colors.

    Returns:
        agraph: A network graph object that can be rendered in a Streamlit app.
    """
    rows = df_net.shape[0]
    frequent_itemsets = apriori(
        df_net, min_support=0.00001, max_len=2, use_colnames=True
    )

    node_list = [
        {"node": next(iter(i["itemsets"])), "support": i["support"]}
        for i in frequent_itemsets.to_dict("records")
        if len(i["itemsets"]) == 1
    ]
    node_dict = {node["node"]: n for n, node in enumerate(node_list)}

    nodes = []
    for node in node_list:
        nodes.append(
            Node(
                id=node_dict[node["node"]],
                size=node["support"] * 50,
                label=node["node"],
                title=f'{node["node"]}: {int(node["support"]*rows)!s}',
                labelHighlightBold=True,
            )
        )

    edges = []
    for edge in frequent_itemsets.to_dict("records"):
        if len(edge["itemsets"]) == 2 and (edge["support"] * rows > 1):
            v1 = next(iter(edge["itemsets"]))
            v2 = list(edge["itemsets"])[1]
            edges.append(
                Edge(
                    source=node_dict[v1],
                    target=node_dict[v2],
                    value=edge["support"],
                    weight=edge["support"],
                    title=f'{v1} <--> {v2}: {int(edge["support"] * rows)}',
                    color=get_edge_color(edge_color_map, v1, v2),
                    type="CURVE_SMOOTH",
                )
            )

    # Create the network graph configuration
    config = Config(
        width=1200,
        height=550,
        directed=True,
        graphviz_layout="fdg",
        edges={"arrows": "none"},
        parentCentralization=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=True,
        node={"labelProperty": "label"},
        link={"labelProperty": "label", "renderLabel": True},
    )

    return agraph(nodes=nodes, edges=edges, config=config)

def return_assoc_rules(df, min_support, sort_by, max_len):
    """
    Generate association rules from a DataFrame using the Apriori algorithm.

    Args:
        df (pandas.DataFrame): The input DataFrame to analyze.
        min_support (float): The minimum support threshold for frequent itemsets.
        sort_by (str): The column name to sort the resulting rules by.
        max_len (int): The maximum length of itemsets to consider.

    Returns:
        pandas.DataFrame: A DataFrame containing the association rules with
        additional metrics, sorted by the specified column.
    """
    frequent_itemsets = apriori(
        df, min_support=min_support, use_colnames=True, max_len=max_len
    )
    assoc_rules = association_rules(frequent_itemsets, min_threshold=0)

    pmi = assoc_rules["support"] / (
        assoc_rules["antecedent support"] * assoc_rules["consequent support"]
    )
    pmi = pmi.apply(lambda x: math.log(x))
    assoc_rules["pmi"] = pmi

    rows = df.shape[0]
    assoc_rules["antecedent count"] = (assoc_rules["antecedent support"] * rows).astype(
        int
    )
    assoc_rules["consequent count"] = (assoc_rules["consequent support"] * rows).astype(
        int
    )
    assoc_rules["support count"] = (assoc_rules["support"] * rows).astype(int)

    assoc_rules = assoc_rules.rename(
        columns={
            "antecedents": "entity_1",
            "consequents": "entity_2",
            "antecedent count": "entity_1_count",
            "consequent count": "entity_2_count",
            "support count": "co-occurrence_count",
        }
    )

    return assoc_rules.sort_values(by=sort_by, ascending=False)

def network_tabular(df, cols_ar):
    """
    Create a tabular representation of network associations.

    Args:
        df (pandas.DataFrame): The input DataFrame containing entity data.
        cols_ar (list): A list of column names to include in the output.

    Returns:
        pandas.DataFrame: A DataFrame containing association rules between entities,
        including only the columns specified in cols_ar.
    """
    df_ar = return_assoc_rules(
        df, min_support=0.00001, sort_by="co-occurrence_count", max_len=2
    )
    df_ar = df_ar.iloc[::2, :].reset_index(drop=True)

    df_ar["entity_1"] = [next(iter(row)) for row in df_ar["entity_1"]]
    df_ar["entity_2"] = [next(iter(row)) for row in df_ar["entity_2"]]

    df_ar = df_ar[cols_ar]

    return df_ar
