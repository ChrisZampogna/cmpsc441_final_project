import re
import json
import ollama
import hashlib
import logging

from pathlib import Path
from types import MethodType
from collections import defaultdict

ollama_seed = lambda x: int(str(int(hashlib.sha512(x.encode()).hexdigest(), 16))[:8])

def pretty_stringify_chat(messages):
  stringified_chat = ''
  for message in messages:
      role = message["role"].capitalize()
      content = message["content"]
      stringified_chat += f"{role}: {content}\n\n\n"
  return stringified_chat

def insert_params(string, **kwargs):
    pattern = r"{{(.*?)}}"
    matches = re.findall(pattern, string)
    for match in matches:
        replacement = kwargs.get(match.strip())
        if replacement is not None:
            string = string.replace("{{" + match + "}}", replacement)
    return string

def tool_tracker(func):
    calls = defaultdict(list)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        calls[f'{func.__name__}_calls'].append({'name': func.__name__, 'args': args, 'kwargs': kwargs, 'result': result})
        print('\n\nTools Called: \n', calls, '\n\n')
        return result
    return wrapper

def run_console_chat(**kwargs):
    chat = AgentTemplate.from_file(**kwargs)
    message = chat.start_chat()
    while True:
        print('Agent:', message)
        try:
            message = chat.send(input('You: '))
        except StopIteration as e:
            if isinstance(e.value, tuple):
                print('Agent:', e.value[0])
                ending_match = e.value[1]
                print('Ending match:', ending_match)
            break

class AgentTemplate:
    def __init__(self, template, **kwargs):
        self.instance = template
        self.instance['options']['seed'] = hash(str(self.instance['options']['seed']))
        self.messages = self.instance['messages']
        self.stop = self.instance['options']['stop'] if 'stop' in self.instance['options'] else None
        self.function_caller = kwargs['function_call_processor'] if 'function_call_processor' in kwargs else None
        process_response_method = kwargs['process_response'] if 'process_response' in kwargs else lambda self, x: x 
        self.process_response = MethodType(process_response_method, self)
        self.parameters = kwargs

    @classmethod
    def from_file(cls, template_file, **kwargs):
        with open(Path(template_file), 'r') as f:
            template = json.load(f)

        return cls(template, **kwargs)

    def completion(self, **kwargs):
        self.parameters |= kwargs
        for item in self.messages:
            item['content'] = insert_params(item['content'], **self.parameters)

        chat_response: ollama.ChatResponse = ollama.chat(**self.instance)
        return chat_response

    def chat_turn(self, **kwargs):
        response = self.completion(**kwargs)
        message = response['message']
        self.messages.append({'role': message.role, 'content': message.content})
        logging.info(f'{message.role}: {message.content}')
        return response 

    def _chat_generator_func(self):
        while True:
            response = self.chat_turn()

            response: ollama.ChatResponse = self.process_response(response)

            if self.stop and any(stop_token in response.message.content for stop_token in self.stop):
                return response.message.content

            user_input = yield response.message.content

            logging.info(f'User: {user_input}')
            self.messages.append({'role': 'user', 'content': user_input})
            if user_input == '/exit':
                break

    def start_chat(self):
        self.chat_generator = self._chat_generator_func()
        first_message = next(self.chat_generator)
        return first_message

    def send(self, user_input):
        return self.chat_generator.send(user_input)