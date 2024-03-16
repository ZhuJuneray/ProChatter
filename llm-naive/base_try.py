import requests
import ipdb
YOUR_GENERATED_SECRET = "Osr1CzACFNG4FX87jAj2:000b7c6e3f9058fe2902caea8a375e53fa7eeea7461128971006f46b39d03932"

url = "https://api.promptperfect.jina.ai/optimize"

headers = {
    "x-api-key": f"token {YOUR_GENERATED_SECRET}",
    "Content-Type": "application/json"
}

payload = {
    "data": {
        "prompt": "中国有哪些地方，哪些地域的菜比较好吃，请给我多推荐几个地方的好吃的私房菜和大众菜。", 
        "targetModel": "chatgpt"
    }
}

response = requests.post(url, headers=headers, json=payload)
ipdb.set_trace()

structured_response = response.json()
optimized_prompt = structured_response['result']['intermediateResults'][0]['promptOptimized']