"""
This module provides functionality for processing and updating Helm values files.

It contains utilities and classes designed to work with values files in Helm charts,
allowing for easy manipulation and updating of configuration values used in Helm deployments.
The module includes functions for converting key lists to dot notation and a ValuesFileProcessor
class for handling Helm values files.
"""

from pathlib import Path
from typing import Dict
from benedict import benedict
from packaging import version
from logzero import logger
import yaml


def convert_key_list_to_dot_notation(key_list: list) -> str:
    """
    Convert a list of keys to dot notation string.

    This function takes a list of keys (which can be strings or integers) and
    converts it to a dot notation string. Integer keys are treated as list indices
    and are enclosed in square brackets.

    Args:
        key_list (list): A list of keys (strings or integers).

    Returns:
        str: A string representing the keys in dot notation.

    Example:
        >>> convert_key_list_to_dot_notation(['a', 0, 'b', 'c'])
        'a[0].b.c'
    """
    result = []
    for key in key_list:
        if isinstance(key, int):
            result.append(f"[{key}]")
        else:
            if result:  # Add a dot only if it's not the first element
                result.append(".")
            result.append(str(key))
    return "".join(result)


class ValuesFileProcessor:
    """
    A class for processing and updating Helm values files.

    This class provides methods to load a Helm values file, check its version,
    and perform operations on the values data.

    Attributes:
        values_file (Path): The path to the Helm values file.
        values_data (Dict): The loaded YAML data from the values file.
        chart_version (str): The version of the chart associated with this values file.
        chart_name (str): The name of the chart associated with this values file.
    """

    def __init__(self, file: Path, chart_version: str, chart_name: str):
        """
        Initialize a new instance to manage Helm chart values.

        Args:
            file (Path): Path object pointing to the values.yaml file location.
            chart_version (str): Version of the Helm chart in semantic versioning
                format (e.g., "1.0.0").
            chart_name (str): Name of the Helm chart being managed.

        Attributes:
            values_file (Path): Stores the path to the values.yaml file.
            values_data (Dict): Contains the parsed YAML data from the values file.
            chart_version (str): Stores the version of the chart.
            chart_name (str): Stores the name of the chart.

        Note:
            - The values_data attribute is populated by calling the _load_yaml() method
              during initialization
            - The values file should be a valid YAML file containing Helm chart values
            - Chart version should follow semantic versioning format

        Example:
            >>> instance = ClassName(
            ...     Path("./values.yaml"),
            ...     "1.2.3",
            ...     "my-chart"
            ... )
        """
        self.values_file = file
        self.values_data = self._load_yaml()
        self.chart_version = chart_version
        self.chart_name = chart_name

    def _load_yaml(self) -> Dict:
        """
        Loads and parses a YAML file into a dictionary using benedict.

        This method opens the YAML file specified by self.values_file and converts it
        into a benedict dictionary, which provides advanced dictionary functionality.

        Returns:
            Dict: A benedict dictionary containing the parsed YAML content.

        Raises:
            Exception: If there are any errors during file opening or YAML parsing.

        Note:
            The method uses benedict with the following configuration:
            - keyattr_dynamic=True: Enables dynamic key attribute access
            - keypath_separator=None: Disables keypath separator
            - format="yaml": Specifies YAML as the input format
        """
        try:
            with open(self.values_file, "r") as f:
                bdict = benedict(
                    f"{f.name}",
                    keyattr_dynamic=True,
                    keypath_separator=None,
                    format="yaml",
                )
                logger.debug(f"Loaded YAML file: {bdict}")
                return bdict
        except Exception as e:
            raise e

    def _save_yaml(self):
        """
        Saves the current values_data dictionary back to the YAML file.

        This method writes the contents of self.values_data to the file specified
        by self.values_file using YAML format. The data is written using safe_dump
        to prevent arbitrary code execution and maintain data integrity.

        Args:
            None

        Returns:
            None

        Raises:
            Exception: If there are any errors during file writing or YAML dumping.

        Note:
            - Uses yaml.safe_dump instead of yaml.dump for security
            - Maintains original order of keys (sort_keys=False)
            - Overwrites the existing file content
        """
        try:
            with open(self.values_file, "w") as f:
                yaml.safe_dump(
                    self.values_data,
                    f,
                    sort_keys=False,
                    encoding="utf-8",
                    allow_unicode=True,
                )
        except Exception as e:
            raise e

    def check_min_version(self, req_min_version: str) -> bool:
        """
        Checks if the current chart version meets the minimum required version.

        Compares the current chart version against a required minimum version
        using semantic versioning rules. The comparison is done using the 'version'
        package's parse functionality.

        Args:
            req_min_version (str): The minimum version requirement to check against,
                in semantic versioning format (e.g., "1.2.3").

        Returns:
            bool: True if the current chart version is greater than or equal to
                the required minimum version, False otherwise.

        Raises:
            Exception: If there are any errors during version parsing or comparison,
                such as invalid version format.

        Example:
            >>> instance.chart_version = "2.0.0"
            >>> instance.check_min_version("1.5.0")
            True
            >>> instance.check_min_version("2.1.0")
            False
        """
        try:
            if version.parse(req_min_version) <= version.parse(self.chart_version):
                return True
            else:
                return False
        except Exception as e:
            raise e

    def add_key(
        self, key: list, overwrite: bool, *overwrite_value, req_min_version: str
    ):
        """
        Adds or updates a key in the YAML values file.

        This method handles the addition or modification of keys in the values file,
        with version checking and optional value overwriting capabilities.

        Args:
            key (list): A list representing the nested key path to add/modify.
                The first element must match the chart name.
            overwrite (bool): If True, allows overwriting existing keys.
                If False, will not modify existing keys.
            *overwrite_value: Variable length argument containing the value to set.
                If not provided, an empty dictionary will be set as the value.
            req_min_version (str): The minimum chart version required for this operation.

        Returns:
            str: Error message if:
                - Chart version doesn't meet minimum requirements
                - Chart name doesn't match the first key element
            None: If the operation completes successfully

        Raises:
            Exception: If there are any errors during the key update process

        Notes:
            - The method logs debug messages for successful operations
            - The method logs error messages for failed operations
            - Keys are converted to dot notation for logging purposes

        Example:
            >>> instance.add_key(['mychart', 'config', 'setting'], True, 'value', '1.0.0')
            # Adds or updates: mychart.config.setting: value
            >>> instance.add_key(['mychart', 'newkey'], False, '1.0.0')
            # Adds mychart.newkey: {} if it doesn't exist
        """
        if not self.check_min_version(req_min_version):
            return (
                f"Chart version {version.parse(self.chart_version)} not eligible for the requirements, "
                f"minimum required version: {version.parse(req_min_version)} at {self.values_file} file."
            )
        if not key[0] == self.chart_name:
            return f"Chart name {self.chart_name} does not match the key {key[0]} at {self.values_file} file."

        key_exists = self.values_data.get(key, None) is not None

        def _update_value():
            if not overwrite_value:
                self.values_data.setdefault(key, {})
            else:
                self.values_data.set(key, *overwrite_value)

        try:
            if not key_exists or (key_exists and overwrite):
                _update_value()
                self._save_yaml()
                action = "overwritten" if key_exists else "added"
                logger.debug(
                    f"Key: {convert_key_list_to_dot_notation(key)} {action} in {self.values_file}"
                )
            else:
                logger.debug(
                    f"Key: {convert_key_list_to_dot_notation(key)} already exists in {self.values_file}"
                )
        except Exception as e:
            logger.error(
                f"Error updating key {convert_key_list_to_dot_notation(key)}: {str(e)}"
            )
            raise

    def remove_key(self, key: list, req_min_version: str):
        """
        Removes a specified key from the YAML values file.

        This method removes a key and its associated value from the values file,
        after performing version compatibility checks and chart name validation.

        Args:
            key (list): A list representing the nested key path to remove.
                The first element must match the chart name.
            req_min_version (str): The minimum chart version required for this operation.

        Returns:
            str: Error message if:
                - Chart version doesn't meet minimum requirements
                - Chart name doesn't match the first key element
            None: If the operation completes successfully

        Raises:
            Exception: If there are any errors during the key removal process

        Notes:
            - The method logs debug messages for both successful removals and when
              the specified key is not found
            - The method logs error messages for failed operations
            - Keys are converted to dot notation for logging purposes
            - Changes are automatically saved to the file after successful removal

        Example:
            >>> instance.remove_key(['mychart', 'config', 'setting'], '1.0.0')
            # Removes mychart.config.setting if it exists
            >>> instance.remove_key(['mychart', 'nonexistent'], '1.0.0')
            # Logs debug message that key was not found
        """
        if not self.check_min_version(req_min_version):
            return (
                f"Chart version {version.parse(self.chart_version)} not eligible for the requirements, "
                f"minimum required version: {version.parse(req_min_version)} at {self.values_file} file."
            )
        if not key[0] == self.chart_name:
            return f"Chart name {self.chart_name} does not match the key {key[0]} at {self.values_file} file."

        try:
            if self.values_data.get(key, None):
                self.values_data.pop(key, None)
                logger.debug(
                    f"Removed {convert_key_list_to_dot_notation(key)} section from {self.values_file}"
                )
                self._save_yaml()
            else:
                logger.debug(
                    f"No {convert_key_list_to_dot_notation(key)} section found in {self.values_file}"
                )
        except Exception as e:
            logger.error(
                f"Error removing key {convert_key_list_to_dot_notation(key)}: {str(e)}"
            )
            raise

    def rename_key(self, old_key: list, key: list, merge: bool, req_min_version: str):
        """
        Renames a key in the YAML values file with optional value merging.

        This method handles the renaming of keys in the values file, with support
        for merging values when both old and new keys exist. It performs version
        compatibility checks and chart name validation before proceeding.

        Args:
            old_key (list): A list representing the nested key path to be renamed.
            key (list): A list representing the new nested key path.
                The first element must match the chart name.
            merge (bool): If True, merges values when the new key already exists.
                For lists: concatenates the lists
                For dicts: merges the dictionaries
                For other types: uses the new value
            req_min_version (str): The minimum chart version required for this operation.

        Returns:
            str: Error message if:
                - Chart version doesn't meet minimum requirements
                - Chart name doesn't match the first key element
            None: If the operation completes successfully or old key doesn't exist

        Raises:
            Exception: If there are any errors during the renaming process

        Notes:
            - The method handles different data types (lists, dicts, other values)
              differently during merging
            - If the old key doesn't exist, the operation is logged and skipped
            - The operation automatically saves changes to the file
            - Keys are converted to dot notation for logging purposes

        Example:
            >>> instance.rename_key(
            ...     ['mychart', 'old', 'config'],
            ...     ['mychart', 'new', 'config'],
            ...     merge=True,
            ...     req_min_version='1.0.0'
            ... )
            # Renames old.config to new.config and merges values if both exist
        """
        if not self.check_min_version(req_min_version):
            return (
                f"Chart version {version.parse(self.chart_version)} not eligible for the requirements, "
                f"minimum required version: {version.parse(req_min_version)} at {self.values_file} file."
            )
        if not key[0] == self.chart_name:
            return f"Chart name {self.chart_name} does not match the key {key[0]} at {self.values_file} file."

        try:
            old_value = self.values_data.get(old_key)

            if old_value is None:
                logger.debug(
                    f"Cannot rename key {convert_key_list_to_dot_notation(old_key)}, because the old key does not exist"
                )
                return

            new_value = self.values_data.get(key)

            if new_value is not None and merge:
                if isinstance(old_value, list) or isinstance(new_value, list):
                    merged_value = new_value + old_value
                elif isinstance(old_value, dict) or isinstance(new_value, dict):
                    merged_value = {**new_value, **old_value}
                else:
                    merged_value = new_value
                self.add_key(key, merge, merged_value, req_min_version=req_min_version)
                logger.debug(
                    f"Merged old values of {convert_key_list_to_dot_notation(old_key)} to {convert_key_list_to_dot_notation(key)} at {self.values_file}"
                )
            elif new_value is not None and not merge:
                self.add_key(key, merge, req_min_version=req_min_version)
            elif new_value is None and merge:
                self.add_key(key, merge, old_value, req_min_version=req_min_version)
            else:
                self.add_key(key, merge, req_min_version=req_min_version)
            self.remove_key(old_key, req_min_version=req_min_version)
            self._save_yaml()

        except Exception as e:
            logger.error(
                f"Error renaming key {convert_key_list_to_dot_notation(old_key)} to {convert_key_list_to_dot_notation(key)}: {str(e)}"
            )
            raise
