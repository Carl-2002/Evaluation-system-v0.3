import time
import pandas as pd
import numpy as np
from openpyxl import load_workbook

from evaluate_model import chat
from caculate import calculate_bleu_and_rouge
from caculate import calculate_and_save_stats

def process_file(file_path, dropdown, socketio, filename, evaluation_path, tishici, use_general_algorithm): # 文字题评测
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名
    
    if '选项A' in df.columns or '模型答案(选择题)' in df.columns or '问题(选择题)' in df.columns:
        error_message = f"此为文字题，请选择文字题文件。"
        socketio.emit('error_2', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序

    required_columns = ['问题(文字题)', '参考', '标准答案(文字题)', '模型名称', '提示词', '模型答案(文字题)', '回答THINK']
    if not all(col in df.columns for col in required_columns):
        error_message = "文件格式不正确，缺少必填列。"
        socketio.emit('error_2', {'message': error_message})
        raise ValueError(error_message)

    total_questions = len(df) * len(dropdown)
    stop_1 = 0
    t = 0

    for model in dropdown:
        print(model)
        score_col = f'{model}分数'
        reason_col = f'{model}原因'
        think_col = f'{model}思考'
        if score_col not in df.columns:
            df[score_col] = None
        if reason_col not in df.columns:
            df[reason_col] = None
        if think_col not in df.columns:
            df[think_col] = None

        for index, row in df.iterrows():
            progress = t / total_questions * 100 
            socketio.emit('progress_2', {'filename': filename, 'progress': progress})
            
            if use_general_algorithm:
                a = pd.notna(row['标准答案(文字题)']) 
            else:
                a = True
            
            if a and pd.notna(row['问题(文字题)']) and pd.notna(row['模型答案(文字题)']): 
                if pd.notna(row['参考']):
                    reference = row['参考']
                else:
                    reference = None
            
                question = row['问题(文字题)']
                answer = row['模型答案(文字题)']
                fenshu, reason, stop, think = chat(question, reference, answer, model, tishici)
                print("####################")
                print(fenshu)
                print("$$$$$$$$$$$$$$$$$$$$")
                print(reason)
                print("********************") 
                print(think)
                print("####################")            
                if stop == 1:
                    stop_1 = 1
                
                df[reason_col] = df[reason_col].astype(str)
                df.at[index, score_col] = fenshu
                df.at[index, reason_col] = str(reason)
                if think is not None:
                    df[think_col] = df[think_col].astype(str)
                    df.at[index, think_col] = str(think)
    
                t = t + 1   

                if t % 25 == 0:
                    df.to_excel(evaluation_path, sheet_name='数据', index=False)
                    print("当前阶段已保存!")     
            else:
                error_message = f"文件格式错误: 第 {index + 1} 行数据不正确。"    
                socketio.emit('error_2', {'message': error_message})
                raise ValueError(error_message)  # 抛出异常以停止程序
    
    socketio.emit('progress_2', {'filename': filename, 'progress': 100})
    df.to_excel(evaluation_path, sheet_name='数据', index=False)
    
    socketio.emit('status_2', {'message': '正在计算通用模型参数......'})
    calculate_and_save_stats(evaluation_path, socketio)
    
    if use_general_algorithm:
        calculate_bleu_and_rouge(evaluation_path, socketio)
    
    if stop_1 == 1:  # 如果有停止标志，则发送停止信号
        socketio.emit('status_2', {'message': '评测中有错误，请检查结果!'})
    else:
        socketio.emit('status_2', {'message': '评测成功!'})


def process_file_solid(file_path, dropdown, socketio, filename, evaluation_path, result_dict, use_general_algorithm):
    df = pd.read_excel(file_path, header=0)  # header=0 表示第一行为列名
    
    if '选项A' in df.columns or '模型答案(选择题)' in df.columns or '问题(选择题)' in df.columns:
        error_message = f"此为文字题，请选择文字题文件。"
        socketio.emit('error_2', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序

    required_columns = ['问题(文字题)', '参考', '标准答案(文字题)', '模型名称', '提示词', '模型答案(文字题)', '回答THINK']
    if not all(col in df.columns for col in required_columns):
        error_message = "文件格式不正确，缺少必填列。"
        socketio.emit('error_2', {'message': error_message})
        raise ValueError(error_message)

    total_questions = len(df) * len(dropdown)
    stop_1 = 0
    t = 0

    for model in dropdown:
        score_col = f'{model}分数'
        reason_col = f'{model}原因'
        think_col = f'{model}思考'
        tishici = result_dict[model]
        print(model)
        print(tishici)
        
        if score_col not in df.columns:
            df[score_col] = None
        if reason_col not in df.columns:
            df[reason_col] = None
        if think_col not in df.columns:
            df[think_col] = None

        for index, row in df.iterrows():
            progress = t / total_questions * 100
            socketio.emit('progress_2', {'filename': filename, 'progress': progress})

            if use_general_algorithm:
                a = pd.notna(row['标准答案(文字题)']) 
            else:
                a = True
            
            if a and pd.notna(row['问题(文字题)']) and pd.notna(row['模型答案(文字题)']): 
                if pd.notna(row['参考']):
                    reference = row['参考']
                else:
                    reference = None
            
                question = row['问题(文字题)']
                answer = row['模型答案(文字题)']
                fenshu, reason, stop, think = chat(question, reference, answer, model, tishici)
                print("####################")
                print(fenshu)
                print("$$$$$$$$$$$$$$$$$$$$")
                print(reason)
                print("********************") 
                print(think)
                print("####################")            
                if stop == 1:
                    stop_1 = 1
                
                df[reason_col] = df[reason_col].astype(str)
                df.at[index, score_col] = fenshu
                df.at[index, reason_col] = str(reason)
                if think is not None:
                    df[think_col] = df[think_col].astype(str)
                    df.at[index, think_col] = str(think)
    
                t = t + 1

                if t % 25 == 0:
                    df.to_excel(evaluation_path, sheet_name='数据', index=False)
                    print("当前阶段已保存!") 
            else:
                error_message = f"文件格式错误: 第 {index + 1} 行数据不正确。"    
                socketio.emit('error_2', {'message': error_message})
                raise ValueError(error_message)  # 抛出异常以停止程序
  
    socketio.emit('progress_2', {'filename': filename, 'progress': 100})
    df.to_excel(evaluation_path, sheet_name='数据', index=False)
    
    socketio.emit('status_2', {'message': '正在计算通用模型参数......'})
    calculate_and_save_stats(evaluation_path, socketio)
    
    if use_general_algorithm:
        calculate_bleu_and_rouge(evaluation_path, socketio)
    
    if stop_1 == 1:  # 如果有停止标志，则发送停止信号
        socketio.emit('status_2', {'message': '评测中有错误，请检查结果!'})
    else:
        socketio.emit('status_2', {'message': '评测成功!'})