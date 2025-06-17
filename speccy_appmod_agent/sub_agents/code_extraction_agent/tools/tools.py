import os

def write_bas_file(filename, content) -> dict:
    """
    Writes the given content to a specified file.

    Args:
        filename (str): The name (and path) of the file to write.
        content (str): The string content to write into the file.

    Returns:
        bool: True if the file was written successfully, False otherwise.
        str: An empty string on success, or an error message on failure.
    """
    try:
        # Ensure the directory exists before writing the file
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

        with open(filename, "w") as f:
            f.write(content)
        print(f"Successfully wrote content to '{filename}'")
        return {"filename": filename}
    except IOError as e:
        error_message = f"Error writing file '{filename}': {e}"
        print(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred while writing '{filename}': {e}"
        print(error_message)
        return False, error_message