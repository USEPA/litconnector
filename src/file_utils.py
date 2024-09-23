import os

import rispy


def write_temp_file(file, file_type):
    """
    Write the contents of an uploaded file to a temporary CSV file.

    Args:
        file (UploadedFile): The uploaded file object from Streamlit.
        file_type (str): The type of the file, used to name the temporary file.

    Returns:
        str: The name of the temporary file created.
    """
    tmp_file_name = "tmp_" + file_type + ".csv"
    with open(tmp_file_name, "w", newline="", encoding="utf-8") as f:
        content = file.getvalue().decode("utf-8")
        f.write(content)
    return tmp_file_name

def load_default_files(sample_file_directory):
    """
    Load default file paths for the application.

    Args:
        sample_file_directory (str): The directory containing sample input files.

    Returns:
        dict: A dictionary with keys representing file types and values representing
              the full file paths to the default files.
    """
    return {
        "distiller_input_file": os.path.join(sample_file_directory, "distiller_tiab_input.csv"),
        "filter_group_file": os.path.join(sample_file_directory, "filter_group_file.csv"),
        "network_config_file": os.path.join(sample_file_directory, "network_config_file.csv"),
        "network_edge_view_options": os.path.join(sample_file_directory, "network_edge_view_options.csv"),
    }

def to_csv_data(df):
    """
    Convert a pandas DataFrame to a CSV string and encode it as UTF-8.

    Args:
        df (pandas.DataFrame): The DataFrame to be converted to CSV.

    Returns:
        bytes: The CSV data encoded as UTF-8 bytes.
    """
    return df.to_csv(index=False).encode("utf-8")

def to_ris_data(df):
    """
    Create RIS-formatted data from a DataFrame.

    Args:
        df (pandas.DataFrame): A DataFrame containing reference information.

    Returns:
        str: A string containing the RIS formatted data.
    """
    entries = []
    for _, row in df.iterrows():
        entry = {
            "type_of_reference": "JOUR",
            "id": str(row["Refid"]),
            "primary_title": row["Title"],
            "abstract": row["Abstract"],
        }
        entries.append(entry)

    return rispy.dumps(entries)
