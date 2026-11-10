from argparse import ArgumentParser
from collections.abc import Sequence

from cinii_research_mcp.cli import run_cli as cinii_cli
from kaken_mcp.cli import run_cli as kaken_cli


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="nii-research-mcp")
    commands = parser.add_subparsers(required=True)
    commands.add_parser("cinii", help="CiNii Research", add_help=False).set_defaults(
        handler=cinii_cli
    )
    commands.add_parser("kaken", help="KAKEN", add_help=False).set_defaults(handler=kaken_cli)
    arguments, remaining = parser.parse_known_args(argv)
    arguments.handler(remaining)
