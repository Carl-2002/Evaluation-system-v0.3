import pandas as pd
from openpyxl import load_workbook

def evaluate_answers(file_path, socketio, evaluation_path):
    df = pd.read_excel(file_path, header=0)
    
    if '模型答案(文字题)' in df.columns or '标准答案(文字题)' in df.columns:
        error_message = f"此为选择题，请选择选择题文件。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)  # 抛出异常以停止程序
    
    if '问题' not in df.columns or '选项A' not in df.columns or '模型答案' not in df.columns or '标准答案' not in df.columns or '参考' not in df.columns or '结果' not in df.columns or '理由' not in df.columns:
        error_message = f"文件格式不正确，缺少必填列。"
        socketio.emit('error', {'message': error_message})
        raise ValueError(error_message)
    
    # 判断模型答案和标准答案是否一致
    for index, row in df.iterrows():
        if pd.notna(row['模型答案']) and pd.notna(row['标准答案']) and pd.isna(row['结果']):
            if row['模型答案'] == row['标准答案']:
                df.at[index, '结果'] = 1  # 如果一致，设置为1
            else:
                df.at[index, '结果'] = 0
        else:
            error_message = f"文件格式: 第 {index + 1} 行数据不正确。"
            socketio.emit('error', {'message': error_message})
            raise ValueError(error_message)  # 抛出异常以停止程序

    
    data = df.to_dict(orient='records')
    total_questions = len(data)
    correct_count = sum(1 for item in data if item['结果'] == 1)
    incorrect_count = total_questions - correct_count
    accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    
    with pd.ExcelWriter(evaluation_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='数据', index=False)
        
        # 获取工作簿和工作表
        workbook = writer.book
        stats_sheet = workbook.create_sheet(title='统计')
 
        # 写入统计信息到指定单元格
        stats_sheet['A1'] = '总题数'
        stats_sheet['A2'] = total_questions
        stats_sheet['B1'] = '正确题数'
        stats_sheet['B2'] = correct_count
        stats_sheet['C1'] = '错误题数'
        stats_sheet['C2'] = incorrect_count
        stats_sheet['D1'] = '正确率'
        stats_sheet['D2'] = accuracy