import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence
from typing import get_args

import httpx

from .client import RecordKind, get_record, search_articles, search_records


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="cinii-research-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser("search-articles", argument_default=SUPPRESS)
    command.add_argument("--query", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.set_defaults(handler=search_articles)

    command = commands.add_parser("search-records", argument_default=SUPPRESS)
    command.add_argument("--query", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--start", type=int)
    command.add_argument("--kind", choices=get_args(RecordKind))
    command.set_defaults(handler=search_records)

    command = commands.add_parser("get-record", argument_default=SUPPRESS)
    command.add_argument("--crid", required=True)
    command.set_defaults(handler=get_record)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
