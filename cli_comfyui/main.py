"""CLI entry point for cli-comfyui."""

import argparse
import sys

from loguru import logger

from cli_comfyui import help_text
from cli_comfyui.commands import init_cmd
from cli_comfyui.commands import result as result_cmd
from cli_comfyui.commands import run as run_cmd
from cli_comfyui.user_paths import get_default_config_path


def _build_parent_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    default_cfg = str(get_default_config_path())
    parent.add_argument(
        "-c",
        "--config",
        default=None,
        metavar="FILE",
        help=(
            f"JSON config path. Default (omit -c): user config at {default_cfg} "
            "(auto-created; platform paths in --help)"
        ),
    )
    parent.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logs to stderr (stdout stays JSON only)",
    )
    return parent


def main(argv: list[str] | None = None) -> int:
    parent = _build_parent_parser()
    parser = argparse.ArgumentParser(
        prog="comfyui-cli",
        description=help_text.MAIN_DESCRIPTION,
        epilog=help_text.build_main_epilog(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parent],
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="subcommands",
        metavar="COMMAND",
        description="init | run | result — use: comfyui-cli COMMAND --help",
    )
    init_cmd.add_parser(subparsers, parents=[parent])
    run_cmd.add_parser(subparsers, parents=[parent])
    result_cmd.add_parser(subparsers, parents=[parent])

    args = parser.parse_args(argv)

    logger.remove()
    level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stderr, level=level)

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
