import os
import re
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

def process_file(file_path, dropdown, socketio, filename, answer_path, tishici):
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名

    if '模型答案(文字题)' in df.columns or '标准答案(文字题)' in df.columns:
        error_message = f"此为选择题，请选择选择题文件。"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    required_columns = ['问题(选择题)', '参考',	'选项A', '选项B', '选项C',	'选项D', '标准答案(选择题)', '模型答案(选择题)']
    if not all(col in df.columns for col in required_columns):
        error_message = "文件格式不正确，缺少必填列。"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)

    print(dropdown)
    load_dotenv()
    api_key = os.getenv(dropdown+'_KEY')
    base_url = os.getenv(dropdown+'_URL')
    model_name = os.getenv(dropdown+'_NAME')

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    
    total_questions = len(df)
    stop_1 = 0
    for index, row in df.iterrows():
        if pd.notna(row['问题(选择题)']) and pd.notna(row['选项A']) and pd.notna(row['选项B']):  
            progress = index / total_questions * 100
            socketio.emit('progress_1', {'filename': filename, 'progress': progress, 'jindu': '正在回答问题({})'.format(index + 1)})
            
            if pd.notna(row['参考']):
                reference = row['参考']
            else:
                reference = None
            
            question = row['问题(选择题)']
            A = row['选项A']
            B = row['选项B']
            C = row['选项C']
            D = row['选项D']
            
            xuanxiang, liyou, stop, think = choose(question, A, B, C, D, reference, client, model_name, tishici)
            print("####################")
            print(xuanxiang)
            print("********************")
            print(liyou)
            print("$$$$$$$$$$$$$$$$$$$$")
            print(think)
            print("####################")
            if stop == 1:
                stop_1 = 1
            df['模型答案(选择题)'] = df['模型答案(选择题)'].astype(str)
            df['理由'] = df['理由'].astype(str)
            df.at[index, '模型答案(选择题)'] = str(xuanxiang)
            df.at[index, '理由'] = str(liyou)
            df.at[index, '字数(理由)'] = len(str(liyou))
            if think is not None:
                df.at[index, '回答THINK'] = str(think)
                df.at[index, '字数(回答THINK)'] = len(str(think))
        else:
            error_message = f"文件格式: 第 {index + 1} 行数据不正确。"
            socketio.emit('error_1', {'message': error_message})
            raise ValueError(error_message)  # 抛出异常以停止程序
    
    socketio.emit('progress_1', {'filename': filename, 'progress': 100, 'jindu': '回答完成!'})
    df.to_excel(answer_path, sheet_name='数据', index=False)
    
    if stop_1 == 1:  # 如果有停止标志，则发送停止信号
        socketio.emit('status_1', {'message': '回答中有错误，请检查结果！(-FFFF)'})
    else:
        socketio.emit('status_1', {'message': '回答成功!'})


def choose(query, A, B, C, D, reference, client, model_name, tishici):
    if reference is not None:
        reference_text = f"你的参考提示:{reference}"
    else:
        reference_text = "你没有参考提示。"
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
        {"role": "system", "content": tishici},
        {"role": "user", "content": f"问题是: {query}\n选项A: {A}\n选项B: {B}\n选项C: {C}\n选项D: {D}\n请根据上述标准作答：" },
        {"role": "user", "content": reference_text},
        ],
        temperature=0.6,
        stream=False,
    )
    time.sleep(1)
    
    result = completion.choices[0].message.content
    
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    print(result)
    
    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, result, re.DOTALL)
    if match:
        result = re.split(r'</think>\s*', result, maxsplit=1, flags=re.DOTALL)[1]
        letter, reason, stop = extract_mark(result)
        return letter, reason, stop, match.group(1).strip()
    else:
        letter, reason, stop = extract_mark(result)
        return letter, reason, stop, reasoning


def extract_mark(response):
    # 找到第一个字母
    letter_match = re.search(r'[A-D]', response, re.DOTALL)
    if letter_match:
        letter = letter_match.group()
        stop = 0
    else:
        letter = '-FFFF'
        stop = 1
    
    # 找到结构 ":" 或 "：" 并提取其后面的内容直到字符串结束
    reason_match = re.search(r'[：:]\s*(.*)', response, re.DOTALL)
    if reason_match:
        reason = reason_match.group(1)
        stop = 0
    else:
        reason = "-FFFF"
        stop = 1
    return letter, reason, stop
