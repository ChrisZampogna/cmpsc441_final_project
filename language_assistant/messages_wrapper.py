from language_assistant.enum.role import Role

class MessagesWrapper():
    def __init__(self, system_prompt: str = ""):
        """
        Initialize the message history with a system prompt.

        Args:
            system_prompt (str): The system prompt to initialize the conversation with.
        """
        self.ollama_messages_list: list[dict] = [{"role": Role.SYSTEM, "content": system_prompt}]

    def get_messages(self) -> list[dict]:
        """
        Return the full conversation history.

        Returns:
            list[dict]: All messages in ollama format.
        """
        return self.ollama_messages_list

    def add_user_message(self, user_input: str) -> None:
        """
        Append a user message to the conversation history.

        Args:
            user_input (str): The user's message content.
        """
        self.ollama_messages_list.append({"role": Role.USER, "content": user_input})

    def add_assistant_message(self, thinking: str, content: str) -> None:
        """
        Append an assistant message to the conversation history.
        The thinking field is omitted if empty.

        Args:
            thinking (str): The model's internal reasoning, or empty string if none.
            content (str): The model's response content.
        """
        self.ollama_messages_list.append({"role": Role.ASSISTANT, "thinking": thinking, "content": content})

    def add_assistant_tool_call_message(self, tool_calls) -> None:
        """
        Append an assistant message containing tool calls to the conversation history.

        Args:
            tool_calls: The tool_calls sequence from the model's response message.
        """
        self.ollama_messages_list.append({"role": Role.ASSISTANT, "content": "", "tool_calls": tool_calls})

    def add_tool_message(self, name: str, content: str) -> None:
        """
        Append a tool result message to the conversation history.

        Args:
            name (str): The name of the tool that was called.
            content (str): The tool's output as a string.
        """
        self.ollama_messages_list.append({"role": "tool", "name": name, "content": content})
