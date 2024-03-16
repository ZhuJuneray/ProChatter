from flask import Flask, render_template, request, jsonify, stream_with_context, Response, session
from flask_session import Session
import json
import requests
from openai import OpenAI
import re
import os
import secrets
import time
import ipdb
import traceback
from bs4 import BeautifulSoup
from difflib import ndiff
import random

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
log_dir = "./log/"
session_id='user_qk'
last_user_input = ""
global_id = 0
question_id = -1
client = OpenAI(api_key="")

# loading questions
original_pool, modified_pool = [], []
local_modified, local_original = '', ''
with open("input.txt", 'r', encoding='utf8') as f:
    for cnt, line in enumerate(f.readlines()):
        if line.startswith("[INPUT]"):
            if local_modified != '':
                modified_pool.append(local_modified)
            local_modified = ''
            local_original += (line.strip("[INPUT] "))
            original = True
        elif line.startswith("[INPUT MODIFIED] "):
            if local_original != '':
                original_pool.append(local_original)
            local_original = ''
            local_modified += (line.strip("[INPUT MODIFIED] "))
            original = False
        else:
            if original:
                local_original += line
            else:
                local_modified += line
if local_original != "":
    original_pool.append(local_original)
if local_modified != "":
    modified_pool.append(local_modified)

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
    response2 = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'user', 'content': user_input}
        ],
        stream=True,
    )
    for event in response2: 
        print(event.choices[0])
        event_text = event.choices[0].delta # EVENT DELTA RESPONSE
        answer = event_text.content # RETRIEVE CONTENT
        # STREAM THE ANSWER
        # sprint(answer, end='', flush=True) # Print the response
        if answer is None:
            answer = '' 
        yield answer.encode('utf-8')

def refine_stream(messages):
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        stream=True
    )
    for event in response:
        print(event.choices[0])
        event_text = event.choices[0].delta
        answer = event_text.content
        # print(answer, end='', flush=True)
        if answer is None:
            answer = ''
        yield answer.encode('utf-8')

@app.route("/generate", methods=['POST'])
def generate():
    user_input = request.form['input']
    global last_user_input
    last_user_input = user_input
    global session_id
    with open(os.path.join(log_dir, session_id + "_user.txt"), "a+") as f:
        f.write(user_input + "\n")
    return Response(generate_stream(user_input), mimetype='text/plain', direct_passthrough=True)
    # answer_response = response2.choices[0].message['content']

timecounter = open(os.path.join(log_dir, "time.txt"), "a+")
@app.route("/highlight", methods=['POST'])
def highlight():
    global session_id
    colors = ['#f7fcf5', '#c7e9c0', '#73c476', '#228a44', '#00441b']
    user_input = request.form['user_input']
    answer_response = request.form['input']
    with open(os.path.join(log_dir, session_id + "_system.txt"), "w") as f:
        f.write(answer_response + "\n")
    while True:
        try:
            response3 = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': user_input},
                    {'role': 'assistant', 'content': answer_response},
                    {'role': 'user', 'content': "对于ChatGPT刚才的回答，答案中哪里可能是ChatGPT理解错误的地方，请标出ChatGPT生成的答案中至少" + str(NUM) + "种且至少五处理解错误程度的词汇、并说出这对应用户提问“" + user_input + "”这句理解模糊的词汇并说明原因。答案格式为：【答案中原词汇】【用户提问中词汇】【1或2或3，代表理解错误程度，数值越大程度越深，要加左右括号】【原因】。\n例如：对于输入“怎样做prompt tuning更结构化的获得结果”，生成结果为“1. 要让prompt tuning更结构化，你可以通过优化prompt模板的设计来获得更好的结果。一种方法是使用预处理技术，例如利用词频统计将常见词组合并为一个token，以减少prompt长度和数量。另一种方法是利用语义相似性，在prompt中添加一些同义词和相关词以提高模型的理解和表达能力。 2. 如果你想要prompt tuning更加结构化，你可以考虑使用更有针对性的prompt，这可以通过对数据集进行分析和研究来实现。你可以观察数据集中的模式和趋势，这可以帮助你确定哪些prompt是最有效的，并指导你进行后续的调整和优化，帮助你获得更好的结果。 3. 一种改进prompt tuning结构的方法是使用GANs，通过对prompt的生成和修改达到更好的效果。GAN可以通过学习和生成高质量的prompt来表现出它们的优化能力。虽然这种方法需要更高水平的技术和资源，但它可以产生更好的结果和更高的效率，因为该方法会利用神经网络生成更优质的prompt。”，给出输出应该类似：“使用GANs】 【prompt tuning更结构化】 【3】 【原因：理解错误】使用GANs并不能直接让prompt tuning更结构化，GANs主要是用于生成和修改模型生成的数据，用于训练模型或增强数据，这与prompt tuning的目的不同。\n【同义词和相关词】 【更有针对性的prompt】 【2】 【原因：理解错误】添加同义词和相关词可以提高模型的理解和表达能力，但并不会让prompt tuning直接变得更有针对性。\n【利用词频统计将常见词组合并为一个token】 【更结构化的获得结果】 【1】 【原因：表述不准确】将常见词组合并为一个token是一种优化prompt的方法，可以减少prompt长度和数量，但不能直接让prompt tuning更结构化的获得结果，只是一种优化方式。”"}
                ]
            )
            annotation_response = response3.choices[0].message['content']
            with open(os.path.join(log_dir, session_id + "_unclear_system.txt"), "a+") as f:
                f.write(annotation_response + "\n")
            print(answer_response, annotation_response)
            ann = annotation_response.split("\n")
            for single_response in ann:
                keywords = re.findall(r'【(.*?)】', single_response)
                if len(keywords) >= 3:
                    regex = re.compile(keywords[0])
                    level = eval(keywords[2])
                    color = colors[level]
                    # 逐个匹配字符串，并记录下标
                    matching_indices = [match.start() for match in regex.finditer(answer_response)]
                    # 遍历匹配到的下标，为其添加高亮样式
                    highlighted_text = ''
                    last_index = 0
                    print(keywords[0], matching_indices, color)
                    for index in matching_indices:
                        # 添加未匹配的文本内容
                        # highlighted_text += f'<span style="background-color: #C2ABC6;">{answer_response[last_index:index]}</span>'
                        highlighted_text += f'{answer_response[last_index:index]}'
                        # 添加高亮的文本内容
                        highlighted_text += f'<span style="background-color: {color};">{keywords[0]}</span>'
                        last_index = index + len(keywords[0])
                        
                    # 添加最后一个未匹配的文本内容
                    highlighted_text += f'{answer_response[last_index:]}'
                    # highlighted_text += f'<span style="background-color: #C2ABC6;">{answer_response[last_index:]}</span>'

                    # 将高亮后的文本以 HTML 形式输出
                    answer_response = highlighted_text
                    # 遍历匹配到的下标，为其添加高亮样式
                    for single_keyword in keywords[1].split("，"):
                        another_text = ''
                        regex = re.compile(single_keyword)
                        last_index = 0
                        another_matching = [match.start() for match in regex.finditer(user_input)]
                        for index in another_matching:
                            # 添加未匹配的文本内容
                            # another_text += f'<span style="background-color: #7F5A83;">{user_input[last_index:index]}</span>'
                            another_text += f'{user_input[last_index:index]}'
                            # 添加高亮的文本内容
                            another_text += f'<span style="background-color: {color};">{keywords[1]}</span>'
                            last_index = index + len(keywords[1])
                        
                        # 添加最后一个未匹配的文本内容
                        # another_text += f'<span style="background-color: #7F5A83;">{user_input[last_index:]}</span>'
                        another_text += f'{user_input[last_index:]}'
                        # 将高亮后的文本以 HTML 形式输出
                        user_input = another_text
            break
        except:
            traceback.print_exc()
            pass
    with open(os.path.join(log_dir, session_id + "_text.txt"), 'a+') as f:
        f.write(user_input + answer_response + "\n")
    # ipdb.set_trace()
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


@app.route('/mark', methods=['POST'])
def marked():
    global session_id
    system_response = request.form['input']
    user_input = request.form['user_input']
    # system_response = open(os.path.join(log_dir, session_id + "_system.txt"), "r").read()
    while True:
        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': '请作为一个评价者，假设有用户的输入是“' + str(user_input) + '”，GPT生成过的答案为“' + str(system_response) + '”，针对GPT刚才的生成说出至少三处GPT的答案对于用户的提问回答的不合适或者不到位，并给出具体到词的修改意见。不要重写答案，只需要给出某一段哪些词修改成哪些词格式的建议就好，但要给出答案哪里写的不合适或者不到位，修改时请指明过去的内容和修改为的内容。格式为：过去的答案/修改后答案。例如，对于答案“”，修改为“过去的答案：\n修改后答案：中国历史悠久，可以追溯到公元前2100年左右的夏朝。以下是一些中国历史的重要事件和朝代\n\n过去的答案：\n修改后答案：商朝时期，商人的地位逐渐上升，商业交流也逐渐发展起来。\n\n”'}   
                ]
            )
            print(response.choices[0].message.content)
            msg = response.choices[0].message.content
            msg_splitted = msg.split("\n\n")
            for item in msg_splitted:
                ipdb.set_trace()
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
                ipdb.set_trace()
            break
        except:
            traceback.print_exc()
            pass
    # ipdb.set_trace()
    print(system_response)
    # ipdb.set_trace()
    return jsonify({"result": system_response})

@app.route('/mark_input', methods=['POST'])
def marked_input():
    global global_id
    global question_id
    user_input = modified_pool[question_id]
    if global_id == 0:
        session_id = request.form['sessionkey']
        patterns = '<select style="display:inline;overflow:hidden;" id="mySelect"><option style="display:none;"></option><option value="option1"></option>'
        user_input = re.sub(patterns, '', user_input)
    elif global_id == 1:
        # 定义正则表达式模式，匹配最近的<select></select>对及其中第二个<option></option>
        pattern = r'<select style="display:inline;overflow:hidden;" id="mySelect">(<option.*?<\/option><option.*?<\/option><option.*?<\/option>)<\/select>(?:(?!<\/?select).)*?'

        # 使用re.findall函数来提取匹配的部分
        matches = re.findall(pattern, user_input, re.DOTALL)

        # 需要删除的<select></select>对数量（这里假设删除一半）
        to_delete_count = len(matches) // 2

        lucky_bin = []
        # 遍历要删除的匹配，提取并保留第二个<option></option>中的内容
        for i in range(to_delete_count):
            while True:
                lucky = random.randint(0, len(matches)-1)
                if lucky not in lucky_bin:
                    break

            lucky_bin.append(lucky)
            match = matches[lucky]
            
            option_content = re.search(r'<option value="option1">(.*?)<\/option><option', match).group(1)
            user_input = user_input.replace(match, option_content)
        patterns = '<select style="display:inline;overflow:hidden;" id="mySelect"><option style="display:none;"></option><option value="option1"></option>'
        user_input = re.sub(patterns, '', user_input)
    elif global_id == 2:
        # 定义正则表达式模式，用于匹配<option style="display:none;"></option>
        pattern = r'<option style="display:none;"></option>'

        # 使用re.sub函数进行替换
        user_input = re.sub(pattern, '', user_input)
        patterns = '<select style="display:inline;overflow:hidden;" id="mySelect"><option style="display:none;"></option><option value="option1"></option>'
        user_input = re.sub(patterns, '', user_input)
    elif global_id == 3:
        session_id = request.form['sessionkey']
        user_input = modified_pool[question_id]
        patterns = '<select style="display:inline;overflow:hidden;" id="mySelect"><option style="display:none;"></option><option value="option1"></option>'
        user_input = re.sub(patterns, '', user_input)
    print(user_input)
    return jsonify({"result": user_input})

@app.route('/index/<param1>/<param2>/', methods=['GET'])
def start(param1, param2):
    global global_id
    global question_id
    global_id = eval(param1) - 1
    question_id = eval(param2) - 1
    session['session_id'] = secrets.token_hex(16)
    return render_template('index.html', session_key=session.get('session_id'), user_input=original_pool[question_id])

@app.route('/', methods=['GET'])
def index():
    return render_template('start.html')

@app.route('/save_version', methods=['POST'])
def save_version():
    global log_dir
    text = request.form['text']
    with open(os.path.join(log_dir, session_id+"_text.txt"), "a+") as f:
        f.write(text + "\n")
    return "OK"

@app.route('/save_ver', methods=['POST'])
def save_ver():
    global log_dir
    global session_id
    input_text = request.form['input']
    answer_text = request.form['answer']
    with open(os.path.join(log_dir, session_id+"_answer.txt"), "a+") as f:
        f.write(input_text + "\n")
    with open(os.path.join(log_dir, session_id+"_input.txt"), "a+") as f:
        f.write(answer_text + "\n")
    return "OK"
    
@app.route("/refine", methods=['POST'])
def refine():
    global last_user_input
    global session_id
    text_now = request.form['input']
    with open(os.path.join(log_dir, session_id+'_text.txt'), "a+") as f:
        f.write("now:" + text_now + "\n")
    # session_id = request.form['sessionkey']
    user_input = last_user_input
    system_response = request.form['answer']
    messages = [
                {'role': 'user', 'content': user_input},
                {'role': 'assistant', 'content': system_response},
                {'role': 'user', 'content': "这是用户的修改部分，你需要依据用户的修改重新生成，特别的<span></span>包裹的区域为用户和上一次生成的系统认为比较模糊的部分：" + text_now}
            ]
    return Response(refine_stream(messages), mimetype='text/plain', direct_passthrough=True)

if __name__ == '__main__':
    app.run(debug=True)
