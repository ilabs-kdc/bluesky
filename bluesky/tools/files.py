"""
Python file with tools for files and folders

Created by: Bob van Dillen
Date: 18-9-2022
"""

import os


def findfile(filename, directory):
    """
    Function: Find a file in a directory
    Args:
        filename:   Name of the file [str]
        directory:  Folder to search in [str]
    Returns:
        If file is found:
            filepath: The path to the file
        Else:
            False

    Created by: Bob van Dillen
    Date: 18-9-2022
    """

    for root, dirs, files in os.walk(directory):

        # Initialize result
        result = False

        # Loop through files
        for f in files:
            if f == filename:
                return os.path.join(root, f)

        # Loop through directories
        for d in dirs:
            result = findfile(filename, os.path.join(root, d))
            if result:
                return result

        return False

