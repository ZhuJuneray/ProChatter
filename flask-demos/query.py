import requests
import openai
import ipdb

openai.api_key = ''

content = "请给我用python的flask生成对应网页。网页中有三个文本框，下面和中间的文本框可以编辑，上面的文本框不能编辑。用户可以点击高亮按钮，点击后选择高亮颜色。选择高亮颜色后用户可以对具体内容进行划选高亮。用户点击生成按钮后需要对http://xxx.xxx.xxx.xxx:5000/chat接口发送POST请求，POST请求内容是json, json的键是user_input，值是用户输入的html。返回结果呈现在上面的文本框中。上面的文本框和下面的文本框每当有新内容的时候，需要同步给中间的文本框，也就是要在中间的文本框中增加新内容。"

response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
        {"role": "system", "content": "You are a helpful coder."},
        {"role": "user", "content": content},
    ]
)

for item in response.items():
    if item[0] == 'choices':
        ipdb.set_trace()
with open("answer.txt", "a+") as f:
    f.write(response.text())