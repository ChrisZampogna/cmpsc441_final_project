import os
import sys
from pathlib import Path

# Disable output buffering so rich/print output appears immediately in all terminals
os.environ.setdefault("PYTHONUNBUFFERED", "1")
sys.stdout.reconfigure(line_buffering=True)  # type: ignore[union-attr]

from client.console import console
from client.chat_wrapper import ChatWrapper
from client.mcp_client import MCPClient
from util.config import load_config

def main():
    console.print("[bold green]Language Assistant starting...[/bold green]")

    config = load_config()
    chat_wrapper: ChatWrapper = ChatWrapper(
        model=config["model"],
        seed="Christopher Zampogna",
        system_prompt=(
            "You are an AI agent who will assist the user with language study. "
            "You have access to tools for looking up words, managing vocabulary lists, and searching grammar references. "
            "Tool use rules: call each tool at most once per user request; never call the same tool with the same arguments twice in one turn; "
            "stop calling tools as soon as you have the information needed to respond; "
            "do not verify an action by calling another tool unless the user explicitly asks you to. "
            "Tool responses use the following status prefixes — treat them as definitive and do not retry: "
            "SUCCESS means the operation completed normally; "
            "DUPLICATE means the item already existed and no action was needed (this is not an error); "
            "NOT FOUND means the item did not exist and no action was taken (this is not an error)."
        ),
        mcp_client=MCPClient(Path("server/mcp_server.py")),
    )

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input == "/exit":
                break
            chat_wrapper.provide_user_input(user_input)
            chat_wrapper.stream_response(prefix="\nAgent: ")
        except Exception:
            console.print_exception()

if __name__ == "__main__":
    main()
