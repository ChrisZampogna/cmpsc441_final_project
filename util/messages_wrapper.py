from util.enum.role import Role

class MessagesWrapper():
    def __init__(self, system_prompt=""):
        self.ollama_messages_list = [{"role": Role.SYSTEM, "content": system_prompt}]

    def get_messages(self):
        return self.ollama_messages_list

    def add_user_message(self, user_input):
        self.ollama_messages_list.append({"role": Role.USER, "content": user_input})

    def add_assistant_message(self, thinking, content):
        self.ollama_messages_list.append({"role": Role.ASSISTANT, "thinking": thinking, "content": content})
