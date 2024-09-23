import io
import os
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st

from data_processing import apply_filters, load_data, preprocess_data
from file_utils import load_default_files, to_csv_data, to_ris_data, write_temp_file
from network_analysis import create_network, network_tabular

SAMPLE_FILE_DIRECTORY = "src/sample_input"


@st.cache_data
def load_and_preprocess_data(file_path):
    df = load_data(file_path)
    return preprocess_data(df)


def main():
    if "selected_files" not in st.session_state:
        st.session_state.selected_files = {}

    if "df_prep" not in st.session_state:
        st.session_state.df_prep = None

    if "selected_filters" not in st.session_state:
        st.session_state.selected_filters = []

    if "filtered_df" not in st.session_state:
        st.session_state.filtered_df = None

    st.set_page_config(page_title="LitConnector", page_icon="📚", layout="wide")

    st.title("LitConnector")

    with st.expander("File Upload Options", expanded=True):
        option = st.radio(
            "Select an option for network creation:",
            ("Upload Your Files", "Try Demo Data"),
        )

        if option == "Upload Your Files":
            handle_file_upload()
        else:
            handle_demo_data()

        if st.session_state.get("files_loaded", False):
            st.session_state.open_network_view = True

    if st.session_state.get("open_network_view", False):
        if st.session_state.df_prep is None:
            with st.spinner("Creating network..."):
                st.session_state.df_prep = load_and_preprocess_data(
                    st.session_state.selected_files["distiller_input_file"]
                )
        create_application()


def handle_file_upload():
    st.subheader("Upload Your Files")
    st.write(
        "Upload custom files for analysis. Example files available for download below."
    )

    # Create a BytesIO object to store the zip file
    zip_io = io.BytesIO()

    # Create a ZipFile object
    with zipfile.ZipFile(
        zip_io, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as zip_file:
        # Add each file in the SAMPLE_FILE_DIRECTORY to the zip
        for file in os.listdir(SAMPLE_FILE_DIRECTORY):
            file_path = os.path.join(SAMPLE_FILE_DIRECTORY, file)
            if os.path.isfile(file_path):
                zip_file.write(file_path, file)

    zip_io.seek(0)

    st.download_button(
        label="Download Example Files",
        data=zip_io,
        file_name="example_litconnector_input.zip",
        mime="application/zip",
    )

    uploaded_files = {
        "distiller_input_file": st.file_uploader(
            "Labelled Title & Abstract Input File",
            type="csv",
            help="**Required columns**: 'Refid' (str), 'Title' (str), 'Abstract' (str), and any category labels you want to use for filtering or network visualization / association analysis.",
        ),
        "filter_group_file": st.file_uploader(
            "Filter Group File (Optional)",
            type="csv",
            help="**Required columns**: 'filter_group_name' (str), 'columns_in_group' (str). \n\n The `filter_group_name` column defines the categories you'd like to filter on (e.g., Species), while `columns_in_group` lists specific levels within each category available for selection (Human, Rodents, etc.)",
        ),
        "network_config_file": st.file_uploader(
            "Network Config File",
            type="csv",
            help="**Required column**: 'columns_in_network'. \n\n This column lists the specific columns from the Distiller file that will be used to create the network. Each row represents a node to be included in the network.",
        ),
        "network_edge_view_options": st.file_uploader(
            "Network Edge View Options",
            type="csv",
            help="_Optional file_ \n\n **Columns**: 'entity_1' (str), 'entity_2' (str), 'edge_color' (str), 'edge_label' (str). \n\n This file defines the colors and labels for edges between entities in the network graph visualization. If not provided, default edge view options will be used.",
        ),
    }

    # Validate uploaded files
    for file_type, uploaded_file in uploaded_files.items():
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                validate_file(file_type, df)
            except Exception as e:
                st.error(f"Error validating {file_type}: {e!s}")

    if st.button("Create Network"):
        required_files = ["distiller_input_file", "network_config_file"]
        if all(uploaded_files[file_type] for file_type in required_files):
            for file_type, uploaded_file in uploaded_files.items():
                uploaded_files[file_type] = write_temp_file(uploaded_file, file_type)

            st.session_state.selected_files = uploaded_files
            st.session_state.files_loaded = True
            st.session_state.df_prep = None  # Reset the preprocessed data
            st.success("Files uploaded successfully")
        else:
            st.error("Please upload all required files.")


def handle_demo_data():
    st.subheader("Try Demo Data")
    st.write("Get started quickly with pre-loaded example files.")

    if st.button("Create Network"):
        st.session_state.selected_files = load_default_files(SAMPLE_FILE_DIRECTORY)
        st.session_state.files_loaded = True
        st.session_state.df_prep = None  # Reset the preprocessed data
        st.success("Files loaded successfully")


def validate_file(file_type, df):
    """
    Validate an uploaded file by checking for required columns based on the file type.

    Args:
        file_type (str): The type of file being validated.
        df (pandas.DataFrame): The DataFrame containing the file data.

    This function checks if the required columns for each file type are present in the
    DataFrame. It displays an error message if any required columns are missing,
    and a success message if all required columns are present.
    """

    if file_type == "distiller_input_file":
        required_columns = ["Refid", "Title", "Abstract"]
    elif file_type == "filter_group_file":
        required_columns = ["filter_group_name", "columns_in_group"]
    elif file_type == "network_config_file":
        required_columns = ["columns_in_network"]
    elif file_type == "network_edge_view_options":
        required_columns = ["entity_1", "entity_2", "edge_color", "edge_label"]
    else:
        st.error(f"Unknown file type: {file_type}")
        return

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(
            f"Error in {file_type}: Missing required columns: {', '.join(missing_columns)}"
        )
    else:
        st.success(f"{file_type} validated successfully")


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


def create_application():
    edge_color_map = create_edge_color_map(
        st.session_state.selected_files["network_edge_view_options"]
    )

    nodes_s6 = pd.read_csv(st.session_state.selected_files["network_config_file"])[
        "columns_in_network"
    ].tolist()
    nodes_unique = list(set(nodes_s6))

    cols_ar = [
        "entity_1",
        "entity_2",
        "entity_1_count",
        "entity_2_count",
        "co-occurrence_count",
        "support",
        "lift",
        "leverage",
        "pmi",
    ]

    # Sidebar for filters
    with st.sidebar:
        st.header("Filters")

        if "filter_group_file" in st.session_state.selected_files:
            filter_groups = pd.read_csv(
                st.session_state.selected_files["filter_group_file"]
            )
            filters = {}

            for group_name in filter_groups["filter_group_name"].unique():
                columns_in_group = filter_groups[
                    filter_groups["filter_group_name"] == group_name
                ]["columns_in_group"].tolist()
                filters[group_name] = st.multiselect(group_name, columns_in_group)

            selected_filters = [
                item for sublist in filters.values() for item in sublist
            ]
        else:
            all_columns = [
                col
                for col in st.session_state.df_prep.columns
                if col not in ["Refid", "Title", "Abstract"]
            ]
            selected_filters = st.multiselect("Select filters", all_columns)

    # Apply filters
    if (
        st.session_state.filtered_df is None
        or selected_filters != st.session_state.selected_filters
    ):
        st.session_state.filtered_df = apply_filters(
            st.session_state.df_prep, selected_filters=selected_filters
        )
        st.session_state.selected_filters = selected_filters

    df_filter = st.session_state.filtered_df

    # Node filters
    col_n1, col_n2 = st.columns([2, 2])
    node1 = col_n1.selectbox("Node 1", ["", *nodes_unique])
    node2 = col_n2.selectbox("Node 2", ["", *nodes_unique])

    if node1 == "" or node2 == "":
        df_filter_net = df_filter
    else:
        df_filter_net = df_filter[(df_filter[node1] == 1) & (df_filter[node2] == 1)]

    # Network details
    col1, col2 = st.columns([3, 1])

    # Network
    with col1:
        df_net = df_filter_net[nodes_unique]
        create_network(df_net, edge_color_map)

        fim = network_tabular(df_filter[nodes_unique], cols_ar)
        fim_filter = fim.loc[(fim["entity_1"] == node1) & (fim["entity_2"] == node2)]
        if fim_filter.shape[0] != 1:
            fim_filter = fim.loc[
                (fim["entity_1"] == node2) & (fim["entity_2"] == node1)
            ]

    # Metrics
    col2.metric("Number of papers", df_filter_net.shape[0])

    ## Table & FIM Metrics

    # Generate markdown string for edge legend
    edge_legend_md = "**Edge Legend:**\n"
    unique_colors = set()
    color_to_labels = {}

    for node1 in edge_color_map:
        for node2 in edge_color_map[node1]:
            color = edge_color_map[node1][node2]["color"]
            label = edge_color_map[node1][node2]["label"]
            unique_colors.add(color)
            if color not in color_to_labels:
                color_to_labels[color] = set()
            color_to_labels[color].add(label)

    for color in unique_colors:
        labels_str = ", ".join(sorted(color_to_labels[color]))
        edge_legend_md += f"- :{color}[**{color.capitalize()}**] = {labels_str}\n"

    if node1 == "" or node2 == "":
        show_net_details = True
        col2.metric("PMI", "N/A")
        col2.metric("Lift", "N/A")
        col2.metric("Leverage", "N/A")
        col2.markdown(edge_legend_md)

    elif (node1 == node2) or (fim_filter.empty):
        show_net_details = True
        df_tiab = df_filter_net[["Refid", "Title", "Abstract"]]
        csv = to_csv_data(df_tiab)
        col2.metric("PMI", "N/A")
        col2.metric("Lift", "N/A")
        col2.metric("Leverage", "N/A")
        col2.markdown(edge_legend_md)
    else:
        show_net_details = False
        tiab_cols = ["Refid", "Title", "Abstract"]
        df_tiab = df_filter_net[tiab_cols]
        csv = to_csv_data(df_tiab)
        col2.metric("PMI", round(fim_filter["pmi"].iloc[0], 3))
        col2.metric("Lift", round(fim_filter["lift"].iloc[0], 3))
        col2.metric("Leverage", round(fim_filter["leverage"].iloc[0], 3))
        col2.markdown(edge_legend_md)

    if show_net_details:
        with st.expander("Network Details"):
            st.subheader("Edges")
            st.write(fim)

    st.subheader("Papers")

    df_tiab = df_tiab.style.format({"Refid": lambda x: "{:.0f}".format(x)})
    st.dataframe(df_tiab)

    current_time = datetime.now().strftime("%m%d%y%H%M%S")
    csv_filename = f"litconnector_export_{current_time}.csv"
    ris_filename = f"litconnector_export_{current_time}.ris"

    st.download_button(
        "Download as .CSV",
        csv,
        csv_filename,
        "text/csv",
        key="download-csv-network",
    )
    ris_data = to_ris_data(df_filter_net[["Refid", "Title", "Abstract"]])
    st.download_button(
        "Download as .RIS",
        ris_data,
        ris_filename,
        "application/x-research-info-systems",
        key="download-ris-network",
    )


if __name__ == "__main__":
    main()
