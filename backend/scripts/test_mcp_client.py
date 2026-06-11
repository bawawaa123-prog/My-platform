from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_PYTHON = r"D:\tools\anaconda\envs\py312\python.exe"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test the local Enterprise Support Agent MCP server as an MCP client.",
    )
    parser.add_argument(
        "--python",
        default=DEFAULT_PYTHON,
        help="Python executable used to launch the local MCP server.",
    )
    parser.add_argument(
        "--server-module",
        default="app.mcp.server",
        help="Python module used to launch the local MCP server.",
    )
    parser.add_argument(
        "--query",
        default="payment order not updated",
        help="Knowledge-base query used for search_knowledge_base.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Top-K value for the knowledge search tool.",
    )
    parser.add_argument(
        "--ticket-id",
        type=int,
        default=None,
        help="Optional ticket ID. If omitted, the script will use the first open ticket returned by MCP.",
    )
    parser.add_argument(
        "--multi-agent-dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether run_multi_agent_ticket_process should use dry_run mode. Defaults to true.",
    )
    return parser.parse_args()


async def run_client_checks(args: argparse.Namespace) -> None:
    transport = StdioTransport(
        command=args.python,
        args=["-m", args.server_module],
        cwd=str(BACKEND_DIR),
        env=dict(os.environ),
    )
    async with Client(transport) as client:
        await client.ping()
        print(f"Connected to MCP server: {client.initialize_result.serverInfo.name}")

        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print("\nAvailable tools:")
        for tool in tools:
            print(f"- {tool.name}")

        print("\nAvailable static resources:")
        if resources:
            for resource in resources:
                print(f"- {resource.uri}")
        else:
            print("- none")

        print("\nAvailable prompts:")
        for prompt in prompts:
            print(f"- {prompt.name}")

        print("\nCalling tool: search_knowledge_base")
        search_result = await client.call_tool(
            "search_knowledge_base",
            {"query": args.query, "top_k": args.top_k},
        )
        print(_format_data(search_result.data))

        ticket_id = args.ticket_id
        if ticket_id is None:
            print("\nCalling tool: list_open_tickets")
            open_tickets_result = await client.call_tool("list_open_tickets", {"limit": 5})
            open_tickets = open_tickets_result.data
            print(_format_data(open_tickets))
            if not open_tickets:
                raise RuntimeError(
                    "No open tickets were returned by MCP. Provide --ticket-id or seed demo data first.",
                )
            ticket_id = int(open_tickets[0]["id"])
            print(f"\nSelected ticket_id={ticket_id} from MCP open ticket list.")

        print(f"\nCalling tool: get_ticket_detail(ticket_id={ticket_id})")
        ticket_detail_result = await client.call_tool("get_ticket_detail", {"ticket_id": ticket_id})
        print(_format_data(ticket_detail_result.data))

        print(
            f"\nCalling tool: run_multi_agent_ticket_process(ticket_id={ticket_id}, "
            f"dry_run={args.multi_agent_dry_run})"
        )
        multi_agent_result = await client.call_tool(
            "run_multi_agent_ticket_process",
            {
                "ticket_id": ticket_id,
                "dry_run": args.multi_agent_dry_run,
            },
        )
        print(_format_data(multi_agent_result.data))

        if not args.multi_agent_dry_run:
            print(f"\nCalling tool: get_agent_audit_trail(ticket_id={ticket_id})")
            audit_result = await client.call_tool("get_agent_audit_trail", {"ticket_id": ticket_id})
            print(_format_data(audit_result.data))


def _format_data(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def main() -> None:
    args = parse_args()
    asyncio.run(run_client_checks(args))


if __name__ == "__main__":
    main()
