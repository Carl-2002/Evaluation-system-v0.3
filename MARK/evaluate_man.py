import pandas as pd
from openpyxl import load_workbook

def caculate_score(file_path, evaluation_path, socketio): # 人工评测，谨慎修改
    socketio.emit('status_3', {'message': '正在计算......'})
    socketio.emit('progress_3', {'progress': 0})
    df = pd.read_excel(file_path)

    required_columns = ['推理思考', '最终答案', '推理字数', '答案字数', '明显幻觉', '模型', '系统提示词']
    if not all(col in df.columns for col in required_columns):
        error_message = "文件格式不正确，缺少必需列!"
        socketio.emit('error_3', {'message': error_message})
        raise ValueError(error_message)

    grouped = df.groupby(['模型', '系统提示词'])

    result_df = pd.DataFrame()

    for name, group in grouped:
        # 计算推理思考和最终答案的平均值
        avg_reasoning = group['推理思考'].mean()
        avg_final_answer = group['最终答案'].mean()

        # 计算两个字数列的平均值
        avg_chars_reasoning = group['推理字数'].mean()
        avg_chars_final_answer = group['答案字数'].mean()

        # 计算字数评分
        total_chars = avg_chars_reasoning + avg_chars_final_answer
        char_diff = abs(total_chars - 1200)
        char_score = char_diff * 0.01

        # 计算幻觉概率
        hallucination_count = (group['明显幻觉'] == '有').sum()
        total_rows = len(group)
        hallucination_probability = hallucination_count / total_rows if total_rows > 0 else 0
        hallucination_score = hallucination_probability * 10

        # 综合评分
        overall_score = (avg_reasoning + avg_final_answer) / 10 * 100 - char_score - hallucination_score

        # 创建一个新的行并添加到结果DataFrame中
        new_row = {
            '模型': name[0],
            '系统提示词': name[1],
            '推理思考平均分': avg_reasoning,
            '最终答案平均分': avg_final_answer,
            '字数平均值': total_chars,
            '幻觉概率': hallucination_probability,
            '综合评分': overall_score
        }
        
        # 使用pd.concat()方法替换append()
        result_df = pd.concat([result_df, pd.DataFrame([new_row])], ignore_index=True)

    result_df = result_df.sort_values(by='综合评分', ascending=False).reset_index(drop=True)
    result_df.insert(0, '序号', range(1, len(result_df) + 1))
    print(result_df)

    with pd.ExcelWriter(evaluation_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='数据', index=False)
        
        workbook = writer.book
        stats_sheet = workbook.create_sheet(title='统计')

        result_df.to_excel(writer, sheet_name='统计', index=False)
    
    socketio.emit('progress_3', {'progress': 100})
    socketio.emit('status_3', {'message': '计算成功!'})