from pathlib import Path

from client.console import console
from client.chat_wrapper import ChatWrapper
from client.mcp_client import MCPClient
from util.config import load_config

def main():
    """
    Entry point for the chat loop.

    Initializes the conversation with a system prompt, then alternates between
    streaming the assistant's response and reading user input until the user
    types '/exit'.
    """

    config = load_config()
    chat_wrapper: ChatWrapper = ChatWrapper(
        model=config["model"],
        seed="Christopher Zampogna",
        system_prompt="You are an AI agent who will assist the user with language study",
        mcp_client=MCPClient(Path("server/mcp_server.py")),
    )
    chat_wrapper.provide_user_input("")

    while True:
        chat_wrapper.stream_response(prefix="\nAgent: ")

        user_input = input("\nYou: ")
        if user_input == "/exit":
            break

        chat_wrapper.provide_user_input(user_input)

if __name__ == "__main__":
    main()
