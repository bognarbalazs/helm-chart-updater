import argparse
import logzero
from logzero import logger
from pathlib import Path
from benedict import benedict
from typing import Dict, Any

from .helm_values import ValuesFileProcessor
from .helm_charts import ChartFileProcessor


def setup_argument_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="helm-chart-updater",
        description="Update Helm chart and values files based on version requirements.",
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="config",
        help="Path of the file that contains the version_changes, defaults to ./version_changes.yaml.",
        default="./version_changes.yaml",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Print debug logs. Overrides --quiet",
        action="store_true",
    )
    parser.add_argument(
        "-q", "--quiet", help="Do not print info logs.", action="store_true"
    )
    parser.add_argument(
        "-lf",
        "--log-file",
        dest="log_file",
        help="Path to the log file. If not provided, logging to file is disabled.",
        default=None,
    )
    return parser.parse_args()


def setup_logging(args: argparse.Namespace) -> None:
    log_format = "%(color)s[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s"
    formatter = logzero.LogFormatter(fmt=log_format)

    if args.verbose:
        log_level = logzero.DEBUG
    elif args.quiet:
        log_level = logzero.WARN
    else:
        log_level = logzero.INFO

    # Set up console logging
    logzero.setup_default_logger(level=log_level, formatter=formatter)

    # Set up file logging if log file is specified
    if args.log_file:
        logzero.logfile(
            args.log_file,
            formatter=formatter,
            maxBytes=10**7,  # 10 MB
            backupCount=3,  # Keep 3 backup copies
            encoding="utf-8",
        )
        logger.info(f"Logging to file: {args.log_file}")


def load_config(config_path: str) -> Dict[str, Any]:
    return benedict(
        config_path, keyattr_dynamic=True, keypath_separator=None, format="yaml"
    )


def process_chart(
    chart_file: Path, chart_config: Dict[str, Any], version_changes: Dict[str, Any]
) -> None:
    chart_processor = ChartFileProcessor(
        chart_file,
        chart_config["chart_name"],
        chart_config["min_version"],
        chart_config["max_version"],
    )
    if chart_processor.get_chart_version() is None:
        logger.info(
            f"{chart_config['chart_name']} dependency not found in the {chart_file} file"
        )
        return

    logger.info(chart_processor.update_chart_version(chart_config["update_to_version"]))

    values_file = chart_file.parent / "values.yaml"
    values_processor = ValuesFileProcessor(
        values_file, chart_processor.get_chart_version(), chart_config["chart_name"]
    )

    for version, changes in version_changes.items():
        for change in changes:
            process_change(values_processor, change, version)


def process_change(
    values_processor: ValuesFileProcessor, change: Dict[str, Any], version: str
) -> None:
    action = change["action"]
    if action == "add_key":
        values_processor.add_key(
            change["key"],
            change["overwrite"],
            change.get("overwrite_value"),
            req_min_version=version,
        )
    elif action == "rename_key":
        values_processor.rename_key(
            change["old_key"],
            change["new_key"],
            change["merge"],
            req_min_version=version,
        )
    elif action == "remove_key":
        values_processor.remove_key(change["key"], req_min_version=version)
    else:
        logger.error(f"Invalid action: {action}")


def main():
    args = setup_argument_parser()

    try:
        config = load_config(args.config)
        for chart_path in config["base_requirements"]["path_for_charts"]:
            for chart_file in Path(chart_path).rglob("**/Chart.yaml"):
                for chart_config in config["base_requirements"]["version_requirements"]:
                    process_chart(chart_file, chart_config, config["version_changes"])

    except Exception as e:
        logger.exception(f"Exception caught: {e}")


if __name__ == "__main__":
    main()
