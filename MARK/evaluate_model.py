import os
import re
import time
from openai import OpenAI
from dotenv import load_dotenv

def chat(query, reference, answer, ref_answer, dropdown, tishici): # 文字题评测中调用模型的部分
    load_dotenv()
    api_key = os.getenv(dropdown+'_KEY')
    base_url = os.getenv(dropdown+'_URL')
    model_name = os.getenv(dropdown+'_NAME')

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    reference = reference or "无。"
    ref_answer = ref_answer or "无。"
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
        {"role": "system", "content": tishici},
        {"role": "user", "content": f"用户问题:{query}\n\n<待评估模型回答 begin>\n{answer}\n<待评估模型回答 end>\n\n<参考答案 begin>\n{ref_answer}\n<参考答案 end>\n\n<参考内容 begin>\n{reference}\n<参考内容 end>"},
        ],
        temperature=0.6,
        stream=False,
    )
    time.sleep(4)
    
    result = completion.choices[0].message.content
    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)

    pattern = r'<think>(.*?)</think>'
    match = re.search(pattern, result, re.DOTALL)

    if match:
        result = re.split(r'</think>\s*', result, maxsplit=1, flags=re.DOTALL)[1]
        reasoning_content = match.group(1).strip()
    else:
        reasoning_content = reasoning

    score, reason, stop = extract_score_and_reason(result)
    return score, reason, stop, reasoning_content

def extract_score_and_reason(response):
    match = None
    for match in re.finditer(r'[0-5]', response[::-1]): 
        break  
    
    if match:
        score = int(match.group())  # 获取匹配的数字
        stop = 0
    else:
        score = -9999  # 如果没有匹配到，返回默认值
        stop = 1
    
    return score, response, stop


if __name__ == "__main__":
    # 模拟输入参数
    dropdown = "deepseek-v3"  # 评测模型名称，或用 QwQ-32B
    query = "做内毒素检测的器具可以用湿热灭菌法灭菌吗？"
    reference = ""
    answer = "内毒素检测的器具是否可以采用湿热灭菌法灭菌，主要取决于几个因素，包括器具的材质、结构和具体用途。湿热灭菌法（如高压蒸汽灭菌）是一种常用的灭菌方法，适用于耐湿热的物品，能够有效地杀死微生物及其孢子。对于内毒素检测的器具，如果它们是由耐湿热的材料制成，且结构设计适合湿热灭菌条件，那么理论上是可以采用湿热灭菌法进行灭菌的。然而，需要注意以下几点： 1. **材料耐受性**：确保所用材料在高温、高湿环境下不会发生物理或化学变化，比如金属部件可能会生锈，塑料部件可能会变形或变质。 2. **器具结构**：某些复杂的器具，如带有精密管道或孔洞的设备，可能需要特别注意，以确保湿热蒸汽能够完全穿透并达到所有区域，从而实现有效的灭菌。 3. **灭菌参数**：湿热灭菌法通常需要设定一定的温度、压力和时间参数。确保所设定的参数与所使用的器具相匹配，以达到最佳灭菌效果。 4. **残留水分**：湿热灭菌后，应确保器具彻底干燥，避免残余水分对后续实验结果产生影响。 因此，在决定是否使用湿热灭菌法对内毒素检测器具进行灭菌之前，建议查阅相关产品的灭菌指南或制造商的建议，确认该方法是否适用于特定的器具。此外，也可以咨询专业的生物安全或实验室管理人员，以获得更具体和针对性的建议。"
    
    ref_answer = """主要结论：做内毒素不可以使用湿热灭菌。
关键点1：湿热灭菌已经被证明不能有效地除去热原 /细菌内毒素;        
关键点2：【药典通则1143细菌内毒素检查法】规定：“本试验操作过程应防止内毒素的污染。”“ 试验所用的器皿需经处理，以去除可能存在的外源性内毒素。耐热器皿常用干热灭菌法（250℃、至少30 分钟)去除，也可采用其他确证不干扰细商内毒素检查的适宜方法。若使用塑料器具，如微孔板和与微量加样器配套的吸头等，应选用标明无内毒素并且对试验无干扰的器具。"""
    tishici = """你是一个专业的回答质量评估助手。你的任务是根据“参考答案”、“参考内容”，从以下几个角度评估“待评估模型回答”与“参考答案”和“参考内容”之间的含义的相似度，并给出一个综合评分。
1. 准确性：是否理解了问题含义，回答是否准确无误。
2. 完整性：回答是否涵盖了“参考答案”中的所有要点。
3. 清晰度：回答是否表达清晰、易于理解。
4. 相关性：回答是否与问题紧密相关。
5. 逻辑性：回答是否有条理、逻辑清晰。
评分采取5档制（1-5），5分表示非常优秀，1分表示非常差。请按照以下格式输出：理由,不少于20字：(分数)。请给出一个综合评分分数，不要依据每一点单独给分。"""

    reference = reference or "无。"
    ref_answer = ref_answer or "无。"
    
    messages = [
        {"role": "system", "content": tishici},
        {"role": "user", "content": f"用户问题:{query}\n\n<待评估模型回答 begin>\n{answer}\n<待评估模型回答 end>\n\n<参考答案 begin>\n{ref_answer}\n<参考答案 end>\n\n<参考内容 begin>\n{reference}\n<参考内容 end>"},
    ]
    
    # 打印 messages 列表
    print("拼接后的 messages 列表：")
    for msg in messages:
        print(f"Role: {msg['role']}, Content: {msg['content']}")

    try:
        score, reason, stop, reasoning_content = chat(query, reference, answer, ref_answer, dropdown, tishici)
        
        # 打印调试信息
        print("=============================================================")
        print(f"分数: {score}")
        print(f"原因: {reason}")
        print(f"停止标志: {stop}")
        print(f"思考内容: {reasoning_content}")
    except Exception as e:
        # 捕获并打印异常信息
        print(f"调试过程中发生错误: {e}")