from ollama import chat
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from util.llm_utils import ollama_seed as seed

console = Console()

SEED = "Christopher Zampogna"
MODEL = "gemma3:270m"
OPTIONS = {
    "temperature": 0.7,
    "seed": seed(SEED),
}
SYSTEM_PROMPT = "You are an AI agent who will assist the user with language study"


def stream_tokens(messages):
    """
    Stream raw tokens from the model as a generator.

    Args:
        messages (list[dict]): Conversation history in ollama message format.

    Yields:
        tuple[str, str]: A (kind, text) pair where kind is 'thinking' or 'content'
                         and text is the partial token string from the model.
    """
    stream = chat(model=MODEL, messages=messages, stream=True, options=OPTIONS)
    for chunk in stream:
        if chunk.message.thinking:
            yield "thinking", chunk.message.thinking
        elif chunk.message.content:
            yield "content", chunk.message.content


def stream_response(messages):
    """
    Stream the model's response, rendering content as live markdown in the terminal.

    Args:
        messages (list[dict]): Conversation history in ollama message format.

    Returns:
        dict: The completed assistant message with keys 'role', 'thinking', and 'content'.
    """
    thinking = ""
    content = ""

    with Live(console=console, refresh_per_second=15) as live:
        for kind, text in stream_tokens(messages):
            if kind == "thinking":
                if not thinking:
                    console.print("Thinking:")
                console.print(text, end="", style="dim")
                thinking += text
            elif kind == "content":
                content += text
                live.update(Markdown(content))
    return {"role": "assistant", "thinking": thinking, "content": content}


def main():
    """
    Entry point for the chat loop.

    Initializes the conversation with a system prompt, then alternates between
    streaming the assistant's response and reading user input until the user
    types '/exit'.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": ""})  # prompt model to start

    while True:
        console.print("Agent:")
        assistant_message = stream_response(messages)
        messages.append(assistant_message)

        user_input = input("\nYou: ")
        if user_input == "/exit":
            break
        messages.append({"role": "user", "content": user_input})


if __name__ == "__main__":
    main()
