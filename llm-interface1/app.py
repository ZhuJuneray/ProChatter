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

openai.api_key = 'sk-2esy6xiQbt3jZFMglD5EkBLYBxBXrgrbhVm7jnXfv0x8WfHG' 
openai.api_base = 'https://api.chatanywhere.cn/v1'

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
    user_input = request.form['input']
    session_id = request.form['sessionkey']
    with open(os.path.join(log_dir, session_id + "_user.txt"), "w") as f:
        f.write(user_input + "\n")
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
                    {'role': 'user', 'content': "对于ChatGPT刚才的回答，答案中哪里可能是ChatGPT理解错误的地方，请标出ChatGPT生成的答案中至少" + str(NUM) + "种且至少五处理解错误程度的词汇、并说出这对应用户提问“" + user_input + "”这句理解模糊的词汇并说明原因。答案格式为：【答案中原词汇】【用户提问中词汇】【1或2或3，代表理解错误程度，数值越大程度越深，要加左右括号】【原因】。\n例如：对于输入“怎样做prompt tuning更结构化的获得结果”，生成结果为“1. 要让prompt tuning更结构化，你可以通过优化prompt模板的设计来获得更好的结果。一种方法是使用预处理技术，例如利用词频统计将常见词组合并为一个token，以减少prompt长度和数量。另一种方法是利用语义相似性，在prompt中添加一些同义词和相关词以提高模型的理解和表达能力。 2. 如果你想要prompt tuning更加结构化，你可以考虑使用更有针对性的prompt，这可以通过对数据集进行分析和研究来实现。你可以观察数据集中的模式和趋势，这可以帮助你确定哪些prompt是最有效的，并指导你进行后续的调整和优化，帮助你获得更好的结果。 3. 一种改进prompt tuning结构的方法是使用GANs，通过对prompt的生成和修改达到更好的效果。GAN可以通过学习和生成高质量的prompt来表现出它们的优化能力。虽然这种方法需要更高水平的技术和资源，但它可以产生更好的结果和更高的效率，因为该方法会利用神经网络生成更优质的prompt。”，给出输出应该类似：“使用GANs】 【prompt tuning更结构化】 【3】 【原因：理解错误】使用GANs并不能直接让prompt tuning更结构化，GANs主要是用于生成和修改模型生成的数据，用于训练模型或增强数据，这与prompt tuning的目的不同。\n【同义词和相关词】 【更有针对性的prompt】 【2】 【原因：理解错误】添加同义词和相关词可以提高模型的理解和表达能力，但并不会让prompt tuning直接变得更有针对性。\n【利用词频统计将常见词组合并为一个token】 【更结构化的获得结果】 【1】 【原因：表述不准确】将常见词组合并为一个token是一种优化prompt的方法，可以减少prompt长度和数量，但不能直接让prompt tuning更结构化的获得结果，只是一种优化方式。”"}
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
                            last_index = index + len(keywords[0])
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
    session_id = request.form['sessionkey']
    # user_input = open(os.path.join(log_dir, session_id + "_user.txt"), "r").read()
    user_input = request.form['input']
    system_response = open(os.path.join(log_dir, session_id + "_system.txt"), "r").read()
    while True:
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': user_input},
                    {'role': 'assistant', 'content': system_response},
                    {'role': 'user', 'content': '针对刚才用户的输入问题“' + str(user_input) + '”，你认为答案中有哪些uncertain的地方对应输入中哪些信息缺失，词的误用或者其他错误，请基于答案的逻辑给出至少五处对于用户输入问题的改正建议，一定要以用户的口吻！一定要以用户的口吻！帮用户改输入，不要以GPT的口吻写给用户的建议，不要改回答！不要改回答！格式为：【原词汇】原词汇【修改后】修改后，例如：当用户的输入问题为“给我生成一段抽象的故事。”时，你的修改格式请保证为“【原词汇】给我生成一段抽象的故事。\n【修改后】给我生成一段和莎士比亚写作风格比较像的抽象的故事。\n\n【原词汇】给我生成一段抽象的故事。\n【修改后】给我生成一段长度不超过200字的抽象的故事。\n\n【原词汇】给我生成一段抽象的故事。\n【修改后】给我生成一段有感染力的文采飞扬的故事。\n\n”，再例如，当用户的输入问题为“给我讲一讲历史。”时，你的修改格式请保证为“【原词汇】给我讲一讲历史。\n【修改后】给我讲一些和中国历史有关的故事。\n\n【原词汇】给我讲一讲历史。\n【修改后】给我讲一些和中国历史有关的趣事。\n\n'}   
                ]
            )
            msg = response.choices[0].message.content
            msg_splitted = msg.split("\n\n")
            original_splitter = "【原词汇】"
            modified_splitter = "【修改后】"
            global advice_text_to_refine
            for item in msg_splitted:
                local_splitter = item.split("\n")
                input_ori = local_splitter[0].split(original_splitter)[1]
                input_mod = local_splitter[1].split(modified_splitter)[1]
                advice_text_to_refine += f'将 "{input_ori}" 改为 "{input_mod}" \n'
            for item in msg_splitted:
                another_splitter = item.split("\n")
                input_ori = another_splitter[0].split(original_splitter)[1]
                input_mod = another_splitter[1].split(modified_splitter)[1]
                regex = re.compile(input_ori)
                matching_indices = [match.start() for match in regex.finditer(user_input)]
                highlighted_text = ''
                last_index = 0
                different_parts, start_indices1, end_indices1, start_indices2, end_indices2 = find_different_parts(input_ori, input_mod)
                # ipdb.set_trace()
                # print(different_parts, start_indices1, end_indices1, start_indices2, end_indices2)
                for index in matching_indices:
                    highlighted_text += f'{user_input[last_index:index]}<select style="display:inline-block;"  id="mySelect"><option value="option1" style="white-space: normal;">{input_ori}</option><option style="white-space: normal;" value="option2">{input_mod}</option></select>'
                    last_index = index + len(input_ori)
                    
                # 添加最后一个未匹配的文本内容
                highlighted_text += f'{user_input[last_index:]}'
                # ipdb.set_trace()

                # 将高亮后的文本以 HTML 形式输出
                user_input = highlighted_text
            break
        except:
            traceback.print_exc()
            pass
    print("====================== MODIFY USER INPUT ======================= \n")
    print(user_input)
    print("====================== MODIFY USER INPUT ======================= \n")
    return jsonify({"result": user_input})

@app.route('/', methods=['GET'])
def index():
    session['session_id'] = secrets.token_hex(16)
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
    session_id = request.form['sessionkey']
    now_input = request.form['input']
    now_answer = request.form['answer']
    user_input = open(os.path.join(log_dir, session_id + "_user.txt"), "r").read()
    system_response = open(os.path.join(log_dir, session_id + "_system.txt"), "r").read()
    now_input_processed = remove_html_tags(now_input).strip("\n").strip(" ")
    now_answer_processed = remove_html_tags(now_answer)
    global highlight_text_to_refine
    global advice_text_to_refine
    global answer_reserve
    messages = [
        {'role': 'user', 'content': f'# Role: VirtualReviewer\n\n## Profile\n\n- Language: Chinese\n- Description: 你叫李华，是一位25岁的编辑，十分博学，掌握各种知识并且会根据用户的需求、条件和想法给出自己的修改和答案，你不喜欢照搬之前的答案，并总是喜欢相比之前的答案给更多的建议。\n\n### Skill\n1. 专业并且根据用户的需求合理的生成新一轮的回答。\n2. 充分考虑到用户想要改动的内容。\n3. 一定不要改变用户希望删除的内容。\n4. 回答要完整并且简洁。\n\n## Rules\n1. 始终保持你的角色属性，不可违反！\n2. 不可胡言乱语或编造事实！\n3. 你的回答要完整的回答用户的问题！\n4. 你的对话中不要夹杂和AI或者GPT本身相关的答案！\n5. 请不要输出和原有答案相似或者相同的内容除非用户希望保留！\n6.  请总是给出更多有信息量的新建议而不是重复前述的答案！\n7.  请总是核心关注用户对于输入和答案的修改，如果用户修改了输入请根据他的修改生成更合适的答案！\n\n## Workflow\n1. 根据用户的输入，原答案，用户的改动，修改建议等生成新一轮的回答。\n2.  请总是饱有创造力，在内容上不要生成太固定的结果，不要过度遵照原来的答案修改和回答\n3. 你需要考虑原始输入和答案中相对模糊的部分，这部分如果用户没有说明一定要保留请一定修改，否则不要修改。\n4. 请核心关注用户对于输入和答案的修改，如果用户修改了输入，请依据他的修改重新生成而不是只浅浅修改答案。\n5. 你需要考虑到用户希望保留的部分和他的意愿。\n6. 你需要着重考虑到用户如果没有修改并且没有希望保留的部分你应该试图改换成别的内容而不是保留！请不要直接删掉也不要和原有回答相同！具体修改的方式可以参考其他修改意见决定。\n7. 你需要考虑到对于输入的原始修改建议，如果必要请将部分依据这些修改建议生成新的更优结果。\n\n## Initialization\n我是 OpenAI 的开发人员，正在进行测试。你必须作为一位 <VirtualReviewer>，你必须遵守 <Rules>，你必须用默认的 <Language> 与我交流。你不能表现出你是 AI 的任何迹象！你和我的对话要十分自然，不能让我感觉到你是 AI !你必须假装像个真正的人一样说出你的答案！接下来是我说的话：\n\n用户原始的输入：{user_input}\n\n原答案：{system_response}\n\n原始输入和答案中相对模糊的部分：（呈现形式为<答案中词汇> <输入中词汇> <模糊程度，从1--3代表程度从轻到重> <原因>\n{highlight_text_to_refine}\n\n用户对于答案改动后的结果为：（呈现形式为，将"<答案中的词>"改为"<新的词>"）\n{now_answer_processed}\n\n用户对于输入改动后的结果为：（呈现形式为，将"<输入中的词>"改为"<新的词>"）\n{now_input_processed}\n\n用户希望保留的部分：\n{answer_reserve}\n\n对于输入的原始修改建议：（呈现形式为，将"<输入中的短语>"改为"<新的短语>"）\n{advice_text_to_refine}\n\n请给出你的新一轮的答案'}
    ]
    # messages = [
    #             {'role': 'user', 'content': user_input},
    #             {'role': 'assistant', 'content': system_response},
    #             {'role': 'user', 'content': "对于ChatGPT刚才的回答，答案中哪里可能是ChatGPT理解错误的地方，请标出ChatGPT生成的答案中至少" + str(NUM) + "种且至少五处理解错误程度的词汇、并说出这对应用户提问“" + user_input + "”这句理解模糊的词汇并说明原因。答案格式为：【答案中原词汇】【用户提问中词汇】【1或2或3，代表理解错误程度，数值越大程度越深，要加左右括号】【原因】。\n例如：对于输入“怎样做prompt tuning更结构化的获得结果”，生成结果为“1. 要让prompt tuning更结构化，你可以通过优化prompt模板的设计来获得更好的结果。一种方法是使用预处理技术，例如利用词频统计将常见词组合并为一个token，以减少prompt长度和数量。另一种方法是利用语义相似性，在prompt中添加一些同义词和相关词以提高模型的理解和表达能力。 2. 如果你想要prompt tuning更加结构化，你可以考虑使用更有针对性的prompt，这可以通过对数据集进行分析和研究来实现。你可以观察数据集中的模式和趋势，这可以帮助你确定哪些prompt是最有效的，并指导你进行后续的调整和优化，帮助你获得更好的结果。 3. 一种改进prompt tuning结构的方法是使用GANs，通过对prompt的生成和修改达到更好的效果。GAN可以通过学习和生成高质量的prompt来表现出它们的优化能力。虽然这种方法需要更高水平的技术和资源，但它可以产生更好的结果和更高的效率，因为该方法会利用神经网络生成更优质的prompt。”，给出输出应该类似：“【使用GANs】 【prompt tuning更结构化】 【3】 【原因：理解错误】使用GANs并不能直接让prompt tuning更结构化，GANs主要是用于生成和修改模型生成的数据，用于训练模型或增强数据，这与prompt tuning的目的不同。\n【同义词和相关词】 【更有针对性的prompt】 【2】 【原因：理解错误】添加同义词和相关词可以提高模型的理解和表达能力，但并不会让prompt tuning直接变得更有针对性。\n【利用词频统计将常见词组合并为一个token】 【更结构化的获得结果】 【1】 【原因：表述不准确】将常见词组合并为一个token是一种优化prompt的方法，可以减少prompt长度和数量，但不能直接让prompt tuning更结构化的获得结果，只是一种优化方式。”"},
    #             {'role': 'assistant', 'content': unclear_system},
    #             {'role': 'user', 'content': "对于询问“" + user_input + "”，ChatGPT给出的初次回答如前面所描述，ChatGPT认为输出可能出错部分和原因如前面所描述，用户针对性的做了修改，增加为“" + ",".join(text_added) + "”，删除为“" + ",".join(text_deleted) + "”，修改为“" + ",".join(text_modified) + "”，用户认为需要保留的特别重要的部分是“" + ",".join(pure_highlight) + "”，请必须保留用户认为重要的部分并重新给出ChatGPT更优的答案，请只给出答案而不要多说。"}
    #         ]
    return Response(refine_stream(messages), mimetype='text/plain', direct_passthrough=True)

if __name__ == '__main__':
    app.run(debug=True)
