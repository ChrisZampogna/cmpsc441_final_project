from ollama import chat
from util.llm_utils import pretty_stringify_chat, ollama_seed as seed

def main():
    # Add you code below
    sign_your_name = 'Christopher Zampogna'
    model = 'gemma3:270m'
    options = {"temperature": 0.7}
    messages = [
      {'role': 'system', 'content': 'You are an AI agent who will assist the user with language study'},
    ]

    # But before here.
    messages.append({'role':'user', 'content':''}) # An empty user message to prompt the model to start responding.

    options |= {'seed': seed(sign_your_name)}
    # Chat loop
    while True:
      response = chat(model=model, messages=messages, stream=False, options=options)
      # Add your code below
      print(f'Agent: {response.message.content}')
      messages.append({'role': 'assistant', 'content': response.message.content})

      message = {'role': 'user', 'content': input('You: ')}
      messages.append(message) # But before here.
      if messages[-1]['content'] == '/exit':
        break

if __name__ == "__main__":
    main()
