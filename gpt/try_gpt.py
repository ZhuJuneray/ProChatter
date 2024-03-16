api_key = "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"
import os
import time
import openai
openai.api_key = api_key
response = openai.ChatCompletion.create(
    model = 'gpt-3.5-turbo',
    messages=[
        {'role': 'user', 'content': 'Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ...'}
    ],
    # max_tokens=1024,
    temperature=0,
    # top_p=1,
    #  logprobs=5,
    # best_of=5,
    stream=True
)
collected_chunks = []
collected_messages = []
start_time = time.time()
for chunk in response:
    chunk_time = time.time() - start_time
    collected_chunks.append(chunk)
    chunk_message = chunk['choices'][0]['delta']
    collected_messages.append(chunk_message)
    print(f"Message received {chunk_time:.2f} seconds after request: {chunk_message}")
