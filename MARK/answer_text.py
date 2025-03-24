import re
import os
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

from caculate import count_characters

def process_file_free(file_path, dropdown, socketio, filename, answer_path, matches):  
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名

    if '选项A' in df.columns or '问题(选择题)' in df.columns or '模型答案(选择题)' in df.columns:
        error_message = f"此为文字题，请选择文字题文件。"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    required_columns = ['问题(文字题)', '参考', '标准答案(文字题)', '模型名称', '提示词', '模型答案(文字题)', '回答THINK']
    if not all(col in df.columns for col in required_columns):
        error_message = "文件格式不正确，缺少必填列。"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)

    lenth = len(df)
    total_questions = len(matches) * lenth * len(dropdown)
    t = 0
    
    df = df.fillna('')
    columns_to_convert = ['问题(文字题)', '参考', '标准答案(文字题)', '模型名称', '提示词', '模型答案(文字题)', '回答THINK']
    df[columns_to_convert] = df[columns_to_convert].astype(str)
    
    for model in dropdown:
        load_dotenv()
        api_key = os.getenv(model+'_KEY')
        base_url = os.getenv(model+'_URL')
        model_name = os.getenv(model+'_NAME')
        
        client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        )
        
        for i, match in enumerate(matches, start=1):
            print(f"Match {i}: {match.strip()}")
            
            for j in range (1, lenth + 1): 
                progress = t / total_questions * 100
                socketio.emit('progress_1', {'filename': filename, 'progress': progress, 'jindu': '正在进行提示词第{}套+{}+问题{}'.format(i, model, j)})
                
                if t <= lenth - 1:
                    if len(df.loc[t, '问题(文字题)']) == 0 or len(df.loc[t, '模型答案(文字题)']) != 0:
                        error_message = f"文件格式: 第{t+1}行数据不正确。"
                        socketio.emit('error_1', {'message': error_message})
                        raise ValueError(error_message)  # 抛出异常以停止程序
                    
                    df.loc[t, '提示词'] = match.strip()
                    df.loc[t, '模型名称'] = model
                else:
                    new_row = {
                        '序号': t + 1,
                        '问题(文字题)': df.loc[t - lenth, '问题(文字题)'],
                        '参考': df.loc[t - lenth, '参考'],
                        '标准答案(文字题)': df.loc[t - lenth, '标准答案(文字题)'],
                        '提示词': match.strip(),
                        '模型名称': model,
                        }
                    df.loc[t] = new_row
                
                reference = df.loc[t, '参考'] if pd.notna(df.loc[t, '参考']) else None
                question = df.loc[t, '问题(文字题)']

                response, think= chat(question, reference, client, model_name, match.strip())
                print("####################")
                print(think)
                print("********************")
                print(response)
                print("####################")
                df.loc[t, '模型答案(文字题)'] = response
                df.loc[t, '字数(模型答案)'] = count_characters(response)
                if think is not None:
                    df.loc[t, '回答THINK'] = think
                    df.loc[t, '字数(回答THINK)'] = count_characters(think)

                t = t + 1

    df.to_excel(answer_path, sheet_name='数据', index=False)
    socketio.emit('progress_1', {'filename': filename, 'progress': 100})
    socketio.emit('status_1', {'message': '回答成功!'})


def process_file_solid(file_path, dropdown, socketio, filename, answer_path, result_dict):  
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名

    if '选项A' in df.columns or '问题(选择题)' in df.columns or '模型答案(选择题)' in df.columns:
        error_message = f"此为文字题，请选择文字题文件。"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    required_columns = ['问题(文字题)', '参考', '标准答案(文字题)', '模型名称', '提示词', '模型答案(文字题)', '回答THINK']
    if not all(col in df.columns for col in required_columns):
        error_message = "文件格式不正确，缺少必填列。"
        socketio.emit('error_1', {'message': error_message})
        raise ValueError(error_message)

    lenth = len(df)
    total_questions = lenth * len(dropdown)
    t = 0
    
    df = df.fillna('')
    columns_to_convert = ['问题(文字题)', '参考', '标准答案(文字题)', '模型名称', '提示词', '模型答案(文字题)', '回答THINK']
    df[columns_to_convert] = df[columns_to_convert].astype(str)
    
    for model in dropdown:
        load_dotenv()
        api_key = os.getenv(model+'_KEY')
        base_url = os.getenv(model+'_URL')
        model_name = os.getenv(model+'_NAME')
        
        client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        )
        
        value = result_dict[model]
        print(model)
        print(value)
            
        for j in range (1, lenth + 1): 
            progress = t / total_questions * 100
            socketio.emit('progress_1', {'filename': filename, 'progress': progress, 'jindu': '正在进行{}+问题{}'.format(model, j)})
                
            if t <= lenth - 1:
                if len(df.loc[t, '问题(文字题)']) == 0 or len(df.loc[t, '模型答案(文字题)']) != 0:
                    error_message = f"文件格式: 第{t+1}行数据不正确。"
                    socketio.emit('error_1', {'message': error_message})
                    raise ValueError(error_message)  # 抛出异常以停止程序
                    
                df.loc[t, '提示词'] = value
                df.loc[t, '模型名称'] = model
            else:
                new_row = {
                    '序号': t + 1,
                    '问题(文字题)': df.loc[t - lenth, '问题(文字题)'],
                    '参考': df.loc[t - lenth, '参考'],
                    '标准答案(文字题)': df.loc[t - lenth, '标准答案(文字题)'],
                    '提示词': value,
                    '模型名称': model,
                    }
                df.loc[t] = new_row
                
            reference = df.loc[t, '参考'] if pd.notna(df.loc[t, '参考']) else None
            question = df.loc[t, '问题(文字题)']

            response, think= chat(question, reference, client, model_name, value)
            print("####################")
            print(think)
            print("********************")
            print(response)
            print("####################")
            df.loc[t, '模型答案(文字题)'] = response
            df.loc[t, '字数(模型答案)'] = len(response)
            if think is not None:
                df.loc[t, '回答THINK'] = think
                df.loc[t, '字数(回答THINK)'] = len(think)

            t = t + 1

    df.to_excel(answer_path, sheet_name='数据', index=False)
    socketio.emit('progress_1', {'filename': filename, 'progress': 100})
    socketio.emit('status_1', {'message': '回答成功!'})


def chat(query, reference, client, model_name, tishici):
    if reference is not None:
        reference_text = f"你的参考提示:{reference}"
    else:
        reference_text = "你没有参考提示。"
   
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": tishici},
            {"role": "user", "content": query },
            {"role": "user", "content": reference_text},
        ],
        temperature=0.5,
        stream=False,
    )
    time.sleep(1)
    
    result = completion.choices[0].message.content 
    
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None) 
    pattern = r'<think>(.*?)</think>'
    match_think = re.search(pattern, result, re.DOTALL)
    
    if match_think:
        return re.split(r'</think>\s*', result, maxsplit=1, flags=re.DOTALL)[1], match_think.group(1).strip()
    else:
        return result, reasoning
