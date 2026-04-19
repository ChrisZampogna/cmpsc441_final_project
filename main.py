from ollama import chat
from util.console import console
from util.chat_wrapper import ChatWrapper

def main():
    """
    Entry point for the chat loop.

    Initializes the conversation with a system prompt, then alternates between
    streaming the assistant's response and reading user input until the user
    types '/exit'.
    """
    chat_wrapper: ChatWrapper = ChatWrapper(seed="Christopher Zampogna")
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
