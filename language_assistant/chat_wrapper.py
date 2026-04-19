import hashlib
from typing import Generator
from rich.markdown import Markdown
from rich.live import Live
from ollama import chat

from language_assistant.console import console
from language_assistant.messages_wrapper import MessagesWrapper
from language_assistant.enum.chunk_type import ChunkType
from language_assistant.enum.role import Role

class ChatWrapper():
    def __init__(
        self,
        model: str = "qwen3.5:2b",
        temperature: float = 0.7,
        seed: str | None = None,
        system_prompt: str = "You are an AI Agent. Be helpful to the user.",
        mcp_client=None,
    ):
        """
        Initialize the chat wrapper.

        Args:
            model (str): Ollama model name to use for inference.
            temperature (float): Sampling temperature passed to the model.
            seed (str | None): Optional string to derive a deterministic numeric seed from.
                               If None, no seed is set and the model behaves non-deterministically.
            system_prompt (str): System prompt used to initialize the conversation.
            mcp_client: Optional MCPClient instance. When provided, its tools are passed to
                        the model and any tool calls are dispatched automatically.
        """
        self.messages: MessagesWrapper = MessagesWrapper(system_prompt=system_prompt)
        self.model: str = model
        self.options: dict = {"temperature": temperature}
        self._mcp_client = mcp_client
        self._tools: list[dict] | None = None

        if seed is not None:
            self.options |= {"seed": self.generate_seed(seed)}

        if mcp_client is not None:
            self._tools = mcp_client.get_ollama_tools()

    def generate_seed(self, text: str) -> int:
        """
        Generate a deterministic numeric seed from a string.

        Args:
            text (str): The input string to hash (e.g. a name).

        Returns:
            int: An 8-digit integer derived from the SHA-512 hash of the input.
        """
        return int(str(int(hashlib.sha512(text.encode()).hexdigest(), 16))[:8])

    def stream_tokens(self) -> Generator[tuple[ChunkType, str], None, None]:
        """
        Stream raw tokens from the model as a generator.

        Yields:
            tuple[ChunkType, str]: A (kind, text) pair where kind is ChunkType.THINKING
                                   or ChunkType.CONTENT and text is the partial token string.
        """
        stream = chat(model=self.model, messages=self.messages.get_messages(), stream=True, options=self.options)
        for chunk in stream:
            match chunk.message:
                case msg if msg.thinking:
                    yield ChunkType.THINKING, msg.thinking
                case msg if msg.content:
                    yield ChunkType.CONTENT, msg.content

    def _run_tool_loop(self) -> None:
        """
        Run non-streaming chat turns until the model stops issuing tool calls.
        Each tool call is dispatched via the MCP client and the result appended
        to history before the next turn.
        """
        while True:
            response = chat(
                model=self.model,
                messages=self.messages.get_messages(),
                tools=self._tools,
                stream=False,
                options=self.options,
            )
            msg = response.message
            if not msg.tool_calls:
                break
            self.messages.add_assistant_tool_call_message(msg.tool_calls)
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                arguments = dict(tool_call.function.arguments)
                console.print(f"[dim][tool] {name}({arguments})[/dim]")
                result = self._mcp_client.call_tool(name, arguments)
                self.messages.add_tool_message(name, result)

    def stream_response(self) -> None:
        """
        Stream the model's response, rendering content as live markdown in the terminal.
        Thinking tokens are printed as plain dimmed text. When the stream is complete,
        the assistant message is appended to the conversation history.

        If an MCP client is configured, tool calls are resolved first via a non-streaming
        loop before the final response is streamed.
        """
        if self._tools:
            self._run_tool_loop()

        thinking = ""
        content = ""

        with Live(console=console, refresh_per_second=15) as live:
            for kind, text in self.stream_tokens():
                match kind:
                    case ChunkType.THINKING:
                        thinking += text
                    case ChunkType.CONTENT:
                        content += text
                        live.update(Markdown(content))
        self.messages.add_assistant_message(thinking, content)

    def provide_user_input(self, user_input: str) -> None:
        """
        Append a user message to the conversation history.

        Args:
            user_input (str): The user's message content.
        """
        self.messages.add_user_message(user_input)
