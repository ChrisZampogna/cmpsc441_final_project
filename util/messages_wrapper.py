from util.enum.role import Role

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
