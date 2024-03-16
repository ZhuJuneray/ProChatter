from flask import Flask, request, jsonify
import requests
import openai
import ujson
import ipdb

openai.api_key = ''  # 在 OpenAI 网站上申请的 API 密钥
openai.api_base = "https://api.chatanywhere.cn/v1"

app = Flask(__name__)
app.config['JSONIFY_THRESHOLD'] = 1024*1024

@app.route("/debug", methods=['GET'])
def debug():
    return "no"


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('user_input')
    temperature = float(data.get('temperature', 0.5))
    max_tokens = int(data.get('max_tokens', 256))
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'user',
             'content': user_input}
        ]
    )
    return jsonify({'response': response.choices[0].message['content']}), 200, {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

if __name__ == '__main__':
    app.run()