import jieba
import random
import pandas as pd
from rouge_chinese import Rouge
from nltk.translate.bleu_score import sentence_bleu

def calculate_and_save_stats(file_path):
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=0)

    # 动态识别包含“分数”字样的列
    score_columns = [col for col in df.columns if '分数' in col]
    if not score_columns:
        raise ValueError("Excel文件中没有找到包含“分数”字样的列。")

    # 计算每个组合的平均分数、中位数、标准差，以及字数的统计量
    grouped = df.groupby(['提示词', '模型名称']).agg({
        **{col: ['mean', 'median', 'std'] for col in score_columns},  # 分数列的统计量
        '字数(模型答案)': ['mean']  # 字数列的统计量
    }).reset_index()

    # 展平多级列名，并使用更清晰的命名规则
    grouped.columns = [
        f"{col[1]}_{col[0]}" if col[1] else col[0]  # 格式化为 "统计量_列名"
        for col in grouped.columns
    ]

    # 计算每个组合的综合得分
    num_score_columns = len(score_columns)
    grouped['综合得分'] = (
        sum(grouped[f'mean_{col}'] for col in score_columns) / num_score_columns * 20  # 平均分部分
        - abs(grouped['mean_字数(模型答案)'] - 500) * 0.05  # 字数偏离部分
    )

    sorted_grouped = grouped.sort_values(by='综合得分', ascending=False)
    sorted_grouped = sorted_grouped.reset_index(drop=True).reset_index().rename(columns={'index': '序号'})

    print(sorted_grouped)
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        sorted_grouped.to_excel(writer, sheet_name='统计', index=False)


def calculate_bleu_and_rouge(file_path):
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name=0)

    grouped = df.groupby(['提示词', '模型名称'])[['标准答案(文字题)', '模型答案(文字题)']].apply(
        lambda group: {
            '标准答案列表': group['标准答案(文字题)'].tolist(),  # 提取标准答案列并转为列表
            '模型答案列表': group['模型答案(文字题)'].tolist()   # 提取模型答案列并转为列表
        }
    ).reset_index(name='答案列表')

    grouped[['标准答案列表', '模型答案列表']] = grouped['答案列表'].apply(pd.Series)
    grouped = grouped.drop(columns=['答案列表'])

    bleu_scores_list = []
    rouge_scores_list = []

    for index, row in grouped.iterrows():
        prompt = row['提示词']
        model_name = row['模型名称']
        standard_answers = row['标准答案列表']
        model_answers = row['模型答案列表']

        rouge = calculate_rouge_scores(model_answers, standard_answers)

        number = len(standard_answers)
        if number > 10:
            result_list = random.sample(range(number), 10)
        else:
            result_list = list(range(number))

        bleu_scores = []
        for i in result_list:
            bleu_score = bleu(standard_answers[i], model_answers[i])
            bleu_scores.append(bleu_score)

        avg_bleu_scores = [sum(score)/len(bleu_scores) for score in zip(*bleu_scores)]

        bleu_scores_list.append(avg_bleu_scores)
        rouge_scores_list.append(rouge)

    # 将 BLEU 和 ROUGE 分数添加到数据框中
    grouped['BLEU-1'] = [score[0] for score in bleu_scores_list]
    grouped['BLEU-2'] = [score[1] for score in bleu_scores_list]
    grouped['BLEU-3'] = [score[2] for score in bleu_scores_list]
    grouped['BLEU-4'] = [score[3] for score in bleu_scores_list]

    grouped['ROUGE-1-r'] = [score['rouge-1']['r'] for score in rouge_scores_list]
    grouped['ROUGE-1-p'] = [score['rouge-1']['p'] for score in rouge_scores_list]
    grouped['ROUGE-1-f'] = [score['rouge-1']['f'] for score in rouge_scores_list]
    grouped['ROUGE-2-r'] = [score['rouge-2']['r'] for score in rouge_scores_list]
    grouped['ROUGE-2-p'] = [score['rouge-2']['p'] for score in rouge_scores_list]
    grouped['ROUGE-2-f'] = [score['rouge-2']['f'] for score in rouge_scores_list]
    grouped['ROUGE-L-r'] = [score['rouge-l']['r'] for score in rouge_scores_list]
    grouped['ROUGE-L-p'] = [score['rouge-l']['p'] for score in rouge_scores_list]
    grouped['ROUGE-L-f'] = [score['rouge-l']['f'] for score in rouge_scores_list]

    grouped = grouped.drop(columns=['标准答案列表', '模型答案列表'])
    print(grouped)

    # 保存数据到 Excel
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        grouped.to_excel(writer, sheet_name='指标', index=False)


def bleu(target, inference):
    target_fenci = ' '.join(jieba.cut(target))
    inference_fenci = ' '.join(jieba.cut(inference))

    reference = []  
    candidate = [] 

    reference.append(target_fenci.split())
    candidate = (inference_fenci.split())

    score1 = sentence_bleu(reference, candidate, weights=(1, 0, 0, 0))
    score2 = sentence_bleu(reference, candidate, weights=(0, 1, 0, 0))
    score3 = sentence_bleu(reference, candidate, weights=(0, 0, 1, 0))
    score4 = sentence_bleu(reference, candidate, weights=(0, 0, 0, 1))
    reference.clear()
    
    bleu_score = [score1, score2, score3, score4]
    return bleu_score


def calculate_rouge_scores(hyps, refs):
    if len(hyps) != len(refs):
        raise ValueError("预测文本和参考文本的数量不一致！")

    rouge = Rouge()
    scores = rouge.get_scores(hyps, refs, avg=True)  # 计算平均分数
    
    for key in scores:  # 遍历外层字典的键（如 'rouge-1', 'rouge-2', 'rouge-l'）
        for sub_key in scores[key]:  # 遍历内层字典的键（如 'r', 'p', 'f'）
            if scores[key][sub_key] < 0.001:  # 检查值是否小于 0.001
                scores[key][sub_key] = 0.001  # 如果小于 0.001，则赋值为 0.001(避免出错)

    return scores
