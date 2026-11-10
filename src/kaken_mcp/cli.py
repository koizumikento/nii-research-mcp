import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import get_project, search_projects, search_researchers


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="kaken-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser("search-projects", argument_default=SUPPRESS)
    command.add_argument("--query", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.set_defaults(handler=search_projects)

    command = commands.add_parser("search-researchers", argument_default=SUPPRESS)
    command.add_argument("--name", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.add_argument("--affiliation")
    command.set_defaults(handler=search_researchers)

    command = commands.add_parser("get-project", argument_default=SUPPRESS)
    command.add_argument("--project-number", required=True)
    command.set_defaults(handler=get_project)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
