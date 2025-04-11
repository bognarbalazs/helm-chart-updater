"""
A class for processing and updating Helm chart files.

This class provides methods to load a Helm chart file, check its version,
and update the microservice version if it meets specified criteria.

Attributes:
    chart_file (Path): The path to the Helm chart file.
    chart_data (Dict): The loaded YAML data from the chart file.
    chart_version (str): The current version of the chart.
    chart_min_version (str): The minimum allowed version for updates.
    chart_max_version (str): The maximum allowed version for updates.
"""

from pathlib import Path
from typing import Dict
import yaml
from benedict import benedict
from packaging import version


class ChartFileProcessor:
    """
    A class for processing and updating Helm chart files.

    This class provides methods to load a Helm chart file, check its version,
    and update the microservice version if it meets specified criteria.

    Attributes:
        chart_file (Path): The path to the Helm chart file.
        chart_name (str): The name of the chart being managed.
        chart_data (Dict): The loaded YAML data from the chart file.
        chart_version (str): The current version of the chart.
        chart_min_version (str): The minimum allowed version for updates.
        chart_max_version (str): The maximum allowed version for updates.
    """

    def __init__(
        self,
        file: Path,
        chart_name: str,
        chart_min_version: str,
        chart_max_version: str,
    ):
        """
        Initialize a new instance with Helm chart configuration and version constraints.

        Args:
            file (Path): Path object pointing to the Chart.yaml file location.
            chart_name (str): Name of the Helm chart to manage.
            chart_min_version (str): Minimum allowed version for the chart in semantic
                versioning format (e.g., "1.0.0").
            chart_max_version (str): Maximum allowed version for the chart in semantic
                versioning format (e.g., "2.0.0").

        Attributes:
            chart_file (Path): Stores the path to the Chart.yaml file.
            chart_name (str): Stores the name of the chart being managed.
            chart_data (Dict): Contains the parsed YAML data from the chart file.
            chart_version (str): Current version of the chart, extracted from chart_data.
            chart_min_version (str): Minimum version constraint for the chart.
            chart_max_version (str): Maximum version constraint for the chart.

        Note:
            - The chart_data attribute is populated by calling the _load_yaml() method
              during initialization
            - The chart_version is automatically extracted from the chart data using
              get_chart_version()
            - All version strings should follow semantic versioning format

        Example:
            >>> instance = ClassName(
            ...     Path("./Chart.yaml"),
            ...     "my-chart",
            ...     "1.0.0",
            ...     "2.0.0"
            ... )
        """
        self.chart_file = file
        self.chart_name = chart_name
        self.chart_data = self._load_yaml()
        self.chart_version = self.get_chart_version()
        self.chart_min_version = chart_min_version
        self.chart_max_version = chart_max_version

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
            with open(self.chart_file, "r") as f:
                return benedict(
                    f"{f.name}",
                    keyattr_dynamic=True,
                    keypath_separator=None,
                    format="yaml",
                )
        except Exception as e:
            raise e

    def _save_yaml(self):
        """
        Saves the current chart_data dictionary back to the YAML file.

        This method writes the contents of self.chart_data to the file specified
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
            with open(self.chart_file, "w") as f:
                yaml.safe_dump(self.chart_data, f, sort_keys=False)
        except Exception as e:
            raise e

    def get_chart_version(self) -> str:
        """
        Retrieves the version of the specified chart from the chart data.

        Searches through the chart data for the specified chart name and extracts
        its version information. The search is case-insensitive and allows for
        partial matches.

        Returns:
            str: The version of the chart if found
            None: If the chart is not found or has no version specified

        Notes:
            - Performs a flexible search using the following criteria:
                - Searches in both keys and values
                - Case-insensitive matching
                - Allows partial matches
            - Returns the first matching version found
            - The search is performed using the chart_name specified during initialization

        Example:
            >>> instance.chart_name = "my-chart"
            >>> instance.get_chart_version()
            "1.2.3"

            >>> instance.chart_name = "non-existent-chart"
            >>> instance.get_chart_version()
            None
        """
        search_results = self.chart_data.search(
            f"{self.chart_name}",
            in_keys=True,
            in_values=True,
            exact=False,
            case_sensitive=False,
        )
        if search_results and len(search_results) > 0 and len(search_results[0]) > 0:
            return search_results[0][0].get("version", None)
        else:
            return None

    def version_check(self) -> bool:
        """
        Validates if the current chart version is within the allowed version range.

        Performs a semantic version comparison to ensure the current chart version
        falls within the minimum and maximum version constraints.

        Returns:
            bool: True if the current version is within the allowed range
                  (min_version <= current_version <= max_version),
                  False otherwise.

        Raises:
            Exception: If there are any errors during version parsing, such as:
                - Invalid version format
                - Unable to compare versions
                - Missing version information

        Example:
            >>> instance.chart_min_version = "1.0.0"
            >>> instance.chart_version = "1.5.0"
            >>> instance.chart_max_version = "2.0.0"
            >>> instance.version_check()
            True

            >>> instance.chart_version = "0.9.0"
            >>> instance.version_check()
            False

        Note:
            Uses the 'version' package for semantic version parsing and comparison.
            All versions must be valid semantic version strings.
        """
        try:
            return (
                version.parse(self.chart_min_version)
                <= version.parse(self.chart_version)
                <= version.parse(self.chart_max_version)
            )
        except Exception as e:
            raise e

    def update_chart_version(self, new_version: str) -> str:
        """
        Updates the version of a specific chart dependency in the Chart.yaml file.

        This method attempts to update the version of a chart dependency if it meets
        version requirements and the dependency exists in the chart configuration.

        Args:
            new_version (str): The new version to set for the chart dependency.
                Must be a valid semantic version string.

        Returns:
            str: A message indicating the result of the operation:
                - Success message with new version if update was successful
                - Current version message if already at desired version
                - Error message if dependency not found
                - Error message if version requirements not met

        Raises:
            Exception: If there are any errors during version parsing or file operations

        Notes:
            - Performs version validation before attempting update
            - Checks if the dependency exists in the chart configuration
            - Only updates if the new version is different from current version
            - Automatically saves changes to the chart file
            - Version must meet the requirements: min_version <= version <= max_version

        Example:
            >>> instance.update_chart_version("1.2.3")
            "Chart updated to 1.2.3 version"
            >>> instance.update_chart_version("1.2.3")
            "Chart version is already at the desired version: 1.2.3 at chart.yaml file"
        """
        try:
            if self.version_check() and version.parse(new_version):
                for dep in self.chart_data.get(["dependencies"]):
                    if dep.get(["name"], None) == self.chart_name:
                        if dep.get(["version"], None) != new_version:
                            dep.set(["version"], new_version)
                            self._save_yaml()
                            return f"Chart {self.chart_name} updated to {new_version} version"
                        else:
                            return f"Chart version is already at the desired version: {new_version}  at {self.chart_file} file"
                    else:
                        return f"{self.chart_name} dependency not found in the {self.chart_file} file"
            else:
                return f"Chart version {self.chart_version} not eligible for the requirements {version.parse(self.chart_min_version)} <= {version.parse(self.chart_version)} <= {version.parse(self.chart_max_version)} at {self.chart_file} file to update it's version"
        except Exception as e:
            raise e
