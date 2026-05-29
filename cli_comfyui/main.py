"""CLI entry point for cli-comfyui."""

import argparse
import sys

from loguru import logger

from cli_comfyui.commands import result as result_cmd
from cli_comfyui.commands import run as run_cmd


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        help="Path to JSON config file (default: ./config.json)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="comfyui-cli",
        description="Execute ComfyUI workflows and query results",
    )
    _common_arguments(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)
    run_cmd.add_parser(subparsers)
    result_cmd.add_parser(subparsers)

    args = parser.parse_args(argv)

    logger.remove()
    level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stderr, level=level)

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
