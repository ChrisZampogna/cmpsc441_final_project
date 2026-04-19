import hashlib
from rich.markdown import Markdown
from rich.live import Live
from ollama import chat

from util.console import console
from util.messages_wrapper import MessagesWrapper
from util.enum.chunk_type import ChunkType
from util.enum.role import Role

class ChatWrapper():
    def __init__(
        self,
        model="gemma3:270m",
        temperature=0.7,
        seed=None,
        system_prompt="You are an AI agent who will assist the user with language study"
    ):
        self.messages: MessagesWrapper = MessagesWrapper(system_prompt=system_prompt)

        self.model = model
        self.options = {"temperature": temperature}

        # Optionally use a deterministic seed generated from a string
        if seed is not None:
            self.options |= {"seed": self.generate_seed(seed)}


    def generate_seed(self, text: str):
        """
        Generate a deterministic numeric seed from a string.

        Args:
            text (str): The input string to hash (e.g. a name).

        Returns:
            int: An 8-digit integer derived from the SHA-512 hash of the input.
        """
        return int(str(int(hashlib.sha512(text.encode()).hexdigest(), 16))[:8])

    def stream_tokens(self):
        """
        Stream raw tokens from the model as a generator.

        Args:
            messages (list[dict]): Conversation history in ollama message format.

        Yields:
            tuple[str, str]: A (kind, text) pair where kind is 'thinking' or 'content'
                             and text is the partial token string from the model.
        """
        stream = chat(model=self.model, messages=self.messages.get_messages(), stream=True, options=self.options)
        for chunk in stream:
            match chunk.message:
                case msg if msg.thinking:
                    yield ChunkType.THINKING, msg.thinking
                case msg if msg.content:
                    yield ChunkType.CONTENT, msg.content

    def stream_response(self):
        """
        Stream the model's response, rendering content as live markdown in the terminal.
        When finished, adds the agent's response to the message history

        Args:
            messages (MessagesWrapper): Wrapper around Ollama-format message history

        Returns:
            Nothing
        """
        thinking = ""
        content = ""

        with Live(console=console, refresh_per_second=15) as live:
            for kind, text in self.stream_tokens():
                match kind:
                    case ChunkType.THINKING:
                        if not thinking:
                            console.print("Thinking:")
                        console.print(text, end="", style="dim")
                        thinking += text
                    case ChunkType.CONTENT:
                        content += text
                        live.update(Markdown(content))
        self.messages.add_assistant_message(thinking, content)

    def provide_user_input(self, user_input: str):
        self.messages.add_user_message(user_input)

