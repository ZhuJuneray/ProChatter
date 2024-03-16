import re

# 假设你有一段包含<select></select>部分的字符串
input_string = '''
This is some text.
<select>
  <option>Option 1</option>
  <option style="display:none;"></option>
</select>
More text
<select>
  <option>Option 3</option>
  <option>Option 4</option>
  <option style="display:none;"></option>
</select>
'''

# 定义正则表达式模式，匹配<select></select>对内部包含的<option style="display:none;"></option>
pattern = r'<select>(.*?)<\/select>'
replacement = lambda match: re.sub(r'<option style="display:none;"></option>', '', match.group(1))

# 使用re.sub函数进行替换
output_string = re.sub(pattern, replacement, input_string, flags=re.DOTALL)

# 打印结果
print(output_string)
