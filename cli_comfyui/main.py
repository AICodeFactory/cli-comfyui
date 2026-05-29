"""CLI entry point for cli-comfyui."""

import argparse
import sys

from loguru import logger

from cli_comfyui import help_text
from cli_comfyui.commands import result as result_cmd
from cli_comfyui.commands import run as run_cmd


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        metavar="FILE",
        help="JSON config path (comfyui_url, workflows_dir, API keys). Default: ./config.json",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logs to stderr (stdout stays JSON only)",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="comfyui-cli",
        description=help_text.MAIN_DESCRIPTION,
        epilog=help_text.MAIN_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _common_arguments(parser)

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="subcommands",
        metavar="COMMAND",
        description="run | result — use: comfyui-cli COMMAND --help for request/response schema",
    )
    run_cmd.add_parser(subparsers)
    result_cmd.add_parser(subparsers)

    args = parser.parse_args(argv)

    logger.remove()
    level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stderr, level=level)

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
