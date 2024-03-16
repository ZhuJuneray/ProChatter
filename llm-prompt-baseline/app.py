from flask import Flask, render_template, request, jsonify, stream_with_context, Response, session
from flask_session import Session
import json
import requests
import openai
import re
import os
import secrets
import time
import ipdb
import traceback
from bs4 import BeautifulSoup
from difflib import ndiff

local_time_start = 0.0

openai.api_key = 'sk-GheB7h42VTcUewSgHAK1wpuDcgiBjleCLSBwg1J4NPn5JdzI'
openai.api_base = 'https://api.chatanywhere.cn/v1'
# openai.api_key = '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'
# openai.api_key = 'sk-UecWKOItLpRCnO2IrANlJCNKmNqCb9U3dCZITU7cVND0A1zy'
# openai.api_key = 'sk-TaEO6PkTXXtJEqbWA3SKonNctJ0nZW6twezd2xxs5cYbxxhA' 
# openai.api_base = 'https://api.chatanywhere.cn/v1'

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
log_dir = "./log/"
session_id='user'

if not os.path.exists(log_dir):
    os.mkdir(log_dir)
NUM = 4
COLOR_PALETTE = {0x1C1F26, 0x3B2A4C, 0x7F5A83, 0xA188A6, 0xC2ABC6}

def compare_soup(user_soup1, user_soup2):
    diff = ndiff(str(user_soup1), str(user_soup2))
    pointer1, pointer2 = 0, 0
    added, deleted = [], []
    for line in diff:
        if line.startswith('+'):
            pointer2 += 1
            added.append((pointer2, line))
            # f.write(f'Added: {line}' + "\n")
        elif line.startswith('-'):
            pointer1 += 1
            deleted.append((pointer1, line))
            # f.write(f'Removed: {line}' + "\n")
        else:
            pointer1 += 1
            pointer2 += 1
    pointer_deleted = 0
    real_deleted, real_modified, real_added = [], [], []
    for item in added:
        while pointer_deleted < len(deleted) and deleted[pointer_deleted][0] < item[0]:
            real_deleted.append(deleted[pointer_deleted])
            pointer_deleted += 1
        if pointer_deleted < len(deleted) and (deleted[pointer_deleted][0] == item[0]):
            real_modified.append((deleted[pointer_deleted][1], item[1], item[0]))
        else:
            real_added.append(item)
    while pointer_deleted < len(deleted):
        real_deleted.append(deleted[pointer_deleted])
        pointer_deleted += 1
    return real_deleted, real_modified, real_added

def extract(content):
    words = []  # 存放聚合后的词汇
    # 初始化第一个元组
    if len(content[0]) == 2:
        current_id, current_word = content[0]

        for next_id, next_word in content[1:]:
            if next_id == current_id + 1:  # 如果下个元组ID等于当前元组ID+1，则将单词合并
                current_word += next_word.strip(' +').strip('- ').strip()
                current_id = next_id
            else:  # 否则，将当前单词添加到结果列表中，并使用下一个元组作为当前元组
                words.append(current_word)
                current_id, current_word = next_id, next_word.strip(' +').strip('- ').strip()

        # 添加最后一个单词
        words.append(current_word)
    else:
        _, current_word, current_id = content[0]

        for _, next_word, next_id in content[1:]:
            if next_id == current_id + 1:  # 如果下个元组ID等于当前元组ID+1，则将单词合并
                current_word += next_word.strip(' +').strip('- ').strip()
                current_id = next_id
            else:  # 否则，将当前单词添加到结果列表中，并使用下一个元组作为当前元组
                words.append(current_word)
                current_id, current_word = next_id, next_word.strip(' +').strip('- ').strip()

        # 添加最后一个单词
        words.append(current_word)
    
    return words

def final_extract(user_deleted, user_modified, user_added):
    rt_dt, rt_md, rt_ad = [], [], []
    
    if len(user_deleted) > 0:
        rt_dt = extract(user_deleted)
    if len(user_modified) > 0:
        rt_md = extract(user_modified)
    if len(user_added) > 0:
        rt_ad = extract(user_added)
    
    return rt_dt, rt_md, rt_ad

def generate_stream(user_input):
    response2 = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'user', 'content': user_input}
        ],
        stream=True,
    )
    for event in response2: 
        event_text = event['choices'][0]['delta'] # EVENT DELTA RESPONSE
        answer = event_text.get('content', '') # RETRIEVE CONTENT
        # STREAM THE ANSWER
        # sprint(answer, end='', flush=True) # Print the response 
        yield answer.encode('utf-8')

def refine_stream(messages):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        stream=True
    )
    for event in response:
        print(event)
        event_text = event['choices'][0]['delta']
        answer = event_text.get('content', '')
        print(answer, end='', flush=True)
        yield answer.encode('utf-8')

@app.route("/generate", methods=['POST'])
def generate():
    global local_time_start
    user_input = request.form['input']
    session_id = request.form['sessionkey']
    now_time = str(time.time() - local_time_start)
    with open(os.path.join(log_dir, session_id + "_user.txt"), "w") as f:
        f.write(user_input + "\n")
    with open(os.path.join(log_dir, session_id + "_user_record.txt"), "a+") as f:
        f.write('[' + now_time + "] " + user_input + "\n")
    with open(os.path.join(log_dir, session_id + "_clicked.txt"), "a+") as f:
        f.write('[' + now_time + "] generate\n")
    return Response(generate_stream(user_input), mimetype='text/plain', direct_passthrough=True)
    # answer_response = response2.choices[0].message['content']

timecounter = open(os.path.join(log_dir, "time.txt"), "a+")

# GLOBAL VARIABLE
highlight_text_to_refine = ""
@app.route("/highlight", methods=['POST'])
def highlight():
    session_id = request.form['sessionkey']
    colors = ['#f7fcf5', '#c7e9c0', '#73c476', '#228a44', '#00441b']
    user_input = open(os.path.join(log_dir, session_id + "_user.txt"), "r").read()
    answer_response = request.form['input']
    last_user_input = user_input
    last_answer_response = answer_response
    with open(os.path.join(log_dir, session_id + "_system.txt"), "w") as f:
        f.write(answer_response + "\n")
    while True:
        try:
            response3 = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': user_input},
                    {'role': 'assistant', 'content': answer_response},
                    {'role': 'user', 'content': "对于ChatGPT刚才的回答，答案中哪里可能是ChatGPT理解错误的地方，请标出ChatGPT生成的答案中至少" + str(NUM) + "种且至少二十处理解错误程度的词汇、并说出这对应用户提问“" + user_input + "”这句理解模糊的词汇并说明原因。答案格式为：【答案中原词汇】【用户提问中词汇】【1或2或3，代表理解错误程度，数值越大程度越深，要加左右括号】【原因】。\n例如：对于输入“怎样做prompt tuning更结构化的获得结果”，生成结果为“1. 要让prompt tuning更结构化，你可以通过优化prompt模板的设计来获得更好的结果。一种方法是使用预处理技术，例如利用词频统计将常见词组合并为一个token，以减少prompt长度和数量。另一种方法是利用语义相似性，在prompt中添加一些同义词和相关词以提高模型的理解和表达能力。 2. 如果你想要prompt tuning更加结构化，你可以考虑使用更有针对性的prompt，这可以通过对数据集进行分析和研究来实现。你可以观察数据集中的模式和趋势，这可以帮助你确定哪些prompt是最有效的，并指导你进行后续的调整和优化，帮助你获得更好的结果。 3. 一种改进prompt tuning结构的方法是使用GANs，通过对prompt的生成和修改达到更好的效果。GAN可以通过学习和生成高质量的prompt来表现出它们的优化能力。虽然这种方法需要更高水平的技术和资源，但它可以产生更好的结果和更高的效率，因为该方法会利用神经网络生成更优质的prompt。”，给出输出应该类似：“使用GANs】 【prompt tuning更结构化】 【3】 【原因：理解错误】使用GANs并不能直接让prompt tuning更结构化，GANs主要是用于生成和修改模型生成的数据，用于训练模型或增强数据，这与prompt tuning的目的不同。\n【同义词和相关词】 【更有针对性的prompt】 【2】 【原因：理解错误】添加同义词和相关词可以提高模型的理解和表达能力，但并不会让prompt tuning直接变得更有针对性。\n【利用词频统计将常见词组合并为一个token】 【更结构化的获得结果】 【1】 【原因：表述不准确】将常见词组合并为一个token是一种优化prompt的方法，可以减少prompt长度和数量，但不能直接让prompt tuning更结构化的获得结果，只是一种优化方式。”"}
                ]
            )
            annotation_response = response3.choices[0].message['content']
            with open(os.path.join(log_dir, session_id + "_unclear_system.txt"), "w") as f:
                f.write(annotation_response + "\n")

            ann = annotation_response.split("\n")
            global highlight_text_to_refine
            highlight_text_to_refine = annotation_response.replace('【', '<').replace('】', '>')
            for counter_class, single_response in enumerate(ann):
                keywords = re.findall(r'【(.*?)】', single_response)
                if len(keywords) >= 3:
                    regex = re.compile(keywords[0])
                    level = eval(keywords[2])
                    regex_input = re.compile(keywords[1])
                    color = colors[level]
                    # 逐个匹配字符串，并记录下标
                    matching_indices = [match.start() for match in regex.finditer(answer_response)]
                    matching_input = [match.start() for match in regex_input.finditer(user_input)]
                    # 遍历匹配到的下标，为其添加高亮样式
                    if len(matching_input) > 0:
                        highlighted_text, highlighted_input = '', ''
                        last_index = 0
                        for index in matching_indices:
                            highlighted_text += f'{answer_response[last_index:index]}'
                            highlighted_text += f'<span style="background-color: {color};" id="class{counter_class}" class="highlight">{keywords[0]}</span>'
                            last_index = index + len(keywords[0])
                        highlighted_text += f'{answer_response[last_index:]}'
                        last_index = 0
                        for index in matching_input:
                            highlighted_input += f'{user_input[last_index:index]}'
                            highlighted_input += f'<span class="highlight" style="background-color: {color};" id="class{counter_class}">{keywords[1]}</span>'
                            last_index = index + len(keywords[1])
                        # 添加最后一个未匹配的文本内容
                        highlighted_input += f'{user_input[last_index:]}'
                        user_input = highlighted_input
                        answer_response = highlighted_text
                        # 遍历匹配到的下标，为其添加高亮样式
                        # for single_keyword in keywords[1].split("，"):
                        #     another_text = ''
                        #     regex = re.compile(single_keyword)
                        #     last_index = 0
                        #     another_matching = [match.start() for match in regex.finditer(user_input)]
                        #     for index in another_matching:
                        #         # 添加未匹配的文本内容
                        #         # another_text += f'<span style="background-color: #7F5A83;">{user_input[last_index:index]}</span>'
                        #         another_text += f'{user_input[last_index:index]}'
                        #         # 添加高亮的文本内容
                        #         another_text += f'<span style="background-color: {color};">{keywords[1]}</span>'
                        #         last_index = index + len(keywords[1])
                            
                        #     # 添加最后一个未匹配的文本内容
                        #     another_text += f'{user_input[last_index:]}'
                        #     # 将高亮后的文本以 HTML 形式输出
                        #     user_input = another_text
            if not (user_input == last_user_input or answer_response == last_answer_response):
                break
        except:
            traceback.print_exc()
            pass
    with open(os.path.join(log_dir, session_id + "_text.txt"), 'w') as f:
        f.write(user_input + answer_response + "\n")
    print("======================= HIGHLIGHT ==================== \n")
    print(user_input)
    print("\n")
    print(answer_response)
    print("======================= HIGHLIGHT ==================== \n")
    return jsonify({"user_input": user_input, "answer": answer_response})

def find_different_parts(str1, str2):
    # 确保str1比str2短，便于遍历
    if len(str1) > len(str2):
        str1, str2 = str2, str1
    
    different_parts = []  # 存储不同的部分
    start_indices1 = []  # 存储str1中不同部分的起始索引
    start_indices2 = []  # 存储str2中不同部分的起始索引
    end_indices1 = []  # 存储str1中不同部分的结束索引
    end_indices2 = []  # 存储str2中不同部分的结束索引
    
    current_part = ""  # 当前的不同部分
    start_index1 = 0  # 当前不同部分在str1中的起始索引
    start_index2 = 0  # 当前不同部分在str2中的起始索引
    
    for i, (char1, char2) in enumerate(zip(str1, str2)):
        if char1 != char2:
            current_part += char2
            if len(current_part) == 1:
                start_index1 = i
                start_index2 = i
        elif current_part:
            different_parts.append(current_part)
            start_indices1.append(start_index1)
            start_indices2.append(start_index2)
            end_indices1.append(i)
            end_indices2.append(i)
            current_part = ""
    
    # 添加str2中剩余的字符作为不同的部分
    if current_part:
        different_parts.append(current_part)
        start_indices1.append(start_index1)
        start_indices2.append(start_index2)
        end_indices1.append(len(str1))
        end_indices2.append(len(str2))

    return different_parts, start_indices1, start_indices2, end_indices1, end_indices2

@app.route('/save_result', methods=['POST'])
def save_result():
    session_id = request.form['sessionkey']
    system_response = request.form['input']
    with open(os.path.join(log_dir, session_id + "_system.txt"), "a+") as f:
        f.write(system_response + "\n")

@app.route('/mark', methods=['POST'])
def marked():
    session_id = request.form['sessionkey']
    system_response = request.form['input']
    user_input = open(os.path.join(log_dir, session_id + "_user.txt"), "r").read()
    # system_response = open(os.path.join(log_dir, session_id + "_system.txt"), "r").read()
    while True:
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': '请作为一个评价者，假设有用户的输入是“' + str(user_input) + '”，GPT生成过的答案为“' + str(system_response) + '”，针对GPT刚才的生成说出至少三处GPT的答案对于用户的提问回答的不合适或者不到位，并给出具体到词的修改意见。不要重写答案，只需要给出某一段哪些词修改成哪些词格式的建议就好，但要给出答案哪里写的不合适或者不到位，修改时请指明过去的内容和修改为的内容。格式为：过去的答案/修改后答案。例如，对于答案“”，修改为“过去的答案：\n修改后答案：中国历史悠久，可以追溯到公元前2100年左右的夏朝。以下是一些中国历史的重要事件和朝代\n\n过去的答案：\n修改后答案：商朝时期，商人的地位逐渐上升，商业交流也逐渐发展起来。\n\n”'}   
                ]
            )
            print(response.choices[0].message.content)
            # ipdb.set_trace()
            msg = response.choices[0].message.content
            msg_splitted = msg.split("\n\n")
            for item in msg_splitted:
                input_splitted = item.split("\n")
                input_ori, input_result = input_splitted[0].split("：")[1], input_splitted[1].split('：')[1]
                print("===================================")
                print(input_ori, input_result)
                regex = re.compile(input_ori)
                matching_indices = [match.start() for match in regex.finditer(system_response)]
                highlighted_text = ''
                last_index = 0
                for index in matching_indices:
                    highlighted_text += f'{system_response[last_index:index]}<select style="display:inline-block;"  id="mySelect"><option value="option1" style="white-space: normal;">{input_ori}</option><option style="white-space: normal;" value="option2">{input_result}</option></select>'
                    last_index = index + len(input_ori)
                highlighted_text += f'{system_response[last_index:]}'
                # too difficult, simplify this thing.
                # different_parts, start_indices1, end_indices1, start_indices2, end_indices2 = find_different_parts(input_ori, input_result)
                # print(different_parts, start_indices1, end_indices1, start_indices2, end_indices2)
                # ipdb.set_trace()
                # for index in matching_indices:
                #     # 添加未匹配的文本内容
                #     # highlighted_text += f'<span style="background-color: #C2ABC6;">{answer_response[last_index:index]}</span>'
                #     highlighted_text += f'{system_response[last_index:index]}'
                #     # 添加高亮的文本内容
                #     highlighted_text += f'{system_response[index:index+start_indices1[0]]}'
                #     last_start_index = start_indices1[0]
                #     last_end_index = end_indices1[0]
                #     for (diff_part, start_index1, end_index1, start_index2, end_index2) in zip(different_parts, start_indices1, end_indices1, start_indices2, end_indices2):
                #         if start_index1 >= last_start_index and end_index1 >= last_end_index:
                #             highlighted_text += f'{system_response[index+last_end_index:index+start_index1]}'
                #         highlighted_text += f'<select style="display:inline;" class="custom-select" id="mySelect"><option value="option1" class="custom-option">{input_ori[start_index1:start_index2]}</option><option value="option2" class="custom-option">{input_result[end_index1:end_index2]}</option></select>'
                #         last_end_index = max(max(start_index2, end_indices2), len(input_ori))
                #     last_index = index + last_end_index
                    
                # # 添加最后一个未匹配的文本内容
                # highlighted_text += f'{system_response[last_index:]}'
                # # ipdb.set_trace()
                # # highlighted_text += f'<span style="background-color: #C2ABC6;">{answer_response[last_index:]}</span>'

                # 将高亮后的文本以 HTML 形式输出
                system_response = highlighted_text
            break
        except:
            traceback.print_exc()
            pass
    print("====================== MODIFY SYSTEM RESPONSE ======================= \n")
    print(system_response)
    print("====================== MODIFY SYSTEM RESPONSE ======================= \n")
    return jsonify({"result": system_response})

# GLOBAL VARIABLE
advice_text_to_refine = ""
@app.route('/mark_input', methods=['POST'])
def marked_input():
    YOUR_GENERATED_SECRET = "Cc24eZkxdA34rGODxNgh:61d6da9dc3aeade181b4f5c564b90d757aff8824ee7f3585caa4a277c89938b0"

    url = "https://api.promptperfect.jina.ai/optimize"

    headers = {
        "x-api-key": f"token {YOUR_GENERATED_SECRET}",
        "Content-Type": "application/json"
    }

    payload = {
        "data": {
            "prompt": request.form['input'], 
            "targetModel": "chatgpt"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    
    structured_response = response.json()
    print(structured_response)
    mod_user_input = f'<select style="display:inline-block;"  id="mySelect"><option value="option1" style="white-space: normal;">{structured_response["result"]["intermediateResults"][0]["promptOptimized"]}</option><option style="white-space: normal;" value="option2">{request.form["input"]}</option></select>'
    with open(os.path.join(log_dir, session_id + "_user_record"), "a+") as f:
        f.write("[" + str(time.time() - local_time_start) + "]" + mod_user_input + "\n")
    return jsonify({"result": mod_user_input})

@app.route('/<param1>', methods=['GET'])
def index(param1):
    global local_time_start
    local_time_start = time.time()
    session['session_id'] = param1
    return render_template('index.html', session_key=session.get('session_id'))

@app.route('/save_version', methods=['POST'])
def save_version():
    text = request.form['text']
    with open(os.path.join(log_dir, session_id+"_text.txt"), "w") as f:
        f.write(text + "\n")
    return "OK"

answer_reserve = ""
@app.route('/save_reserve', methods=['POST'])
def save_reserve():
    global answer_reserve
    text = request.form['text']
    answer_reserve += f'"{text}"\n'
    return "OK"

import re

def remove_html_tags(input_text):
    # 正则表达式匹配要移除的标签
    pattern = r'<\/?(select|option|span)[^>]*>'
    sanitized_text = re.sub(pattern, '', input_text)
    return sanitized_text

@app.route("/refine", methods=['POST'])
def refine():
    messages = [
        {'role': 'user', 'content': request.form['input']}
    ]
    return Response(refine_stream(messages), mimetype='text/plain', direct_passthrough=True)

if __name__ == '__main__':
    app.run(debug=True)
