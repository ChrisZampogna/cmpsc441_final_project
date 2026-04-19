from language_assistant.console import console
from language_assistant.chat_wrapper import ChatWrapper
from language_assistant.mcp_client import MCPClient

def main():
    """
    Entry point for the chat loop.

    Initializes the conversation with a system prompt, then alternates between
    streaming the assistant's response and reading user input until the user
    types '/exit'.
    """
    mcp_client = MCPClient("mcp_server.py")

    chat_wrapper: ChatWrapper = ChatWrapper(
        model="qwen3.5:2b",
        seed="Christopher Zampogna",
        system_prompt="You are an AI agent who will assist the user with language study",
        mcp_client=mcp_client,
    )
    chat_wrapper.provide_user_input("")

    while True:
        console.print("\nAgent: ")
        chat_wrapper.stream_response()

        user_input = input("\nYou: ")
        if user_input == "/exit":
            break

        chat_wrapper.provide_user_input(user_input)

if __name__ == "__main__":
    main()
