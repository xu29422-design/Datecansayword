import os
import pandas as pd
import json
import sys
import io

# 强制设置标准输出编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = "downloads"

def load_and_summarize_data():
    """读取所有 CSV 文件并生成适合大模型阅读的摘要格式"""
    
    all_data_summaries = []
    
    print("📂 正在读取本地数据文件...")
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".csv"):
            continue
            
        filepath = os.path.join(DATA_DIR, filename)
        try:
            df = pd.read_csv(filepath)
            
            # 过滤掉全为 0 的无效数据行（比如周末没数据或者还没到那一天）
            # 假设如果 '曝光 uv' 为 0，说明那天没数据
            if '曝光 uv' in df.columns:
                df = df[df['曝光 uv'] > 0]
                
            if df.empty:
                continue
                
            # 获取数据集的基本信息
            platform = df['端'].iloc[0] if '端' in df.columns else '未知端'
            product = df['产品'].iloc[0] if '产品' in df.columns else '未知产品'
            
            # 将数据转换为紧凑的 JSON 字符串，节省 Token
            # 只保留核心字段，去掉一些冗余的列
            core_columns = ['统计时间', '曝光 uv', '请求uv', '请求成功uv', '采纳 uv', '请求率', '请求成功率', '采纳率']
            available_columns = [col for col in core_columns if col in df.columns]
            
            compact_data = df[available_columns].to_dict(orient='records')
            
            dataset_info = {
                "dataset_name": f"{product} - {platform}端 漏斗数据",
                "date_range": f"{df['统计时间'].min()} 至 {df['统计时间'].max()}",
                "data": compact_data
            }
            
            all_data_summaries.append(dataset_info)
            print(f"✅ 成功加载: {dataset_info['dataset_name']} ({len(compact_data)}天数据)")
            
        except Exception as e:
            print(f"❌ 读取 {filename} 失败: {e}")
            
    return all_data_summaries

def chat_with_data():
    """模拟与大模型的对话交互"""
    data_context = load_and_summarize_data()
    
    if not data_context:
        print("没有找到有效的数据，请先运行采集脚本。")
        return
        
    print("\n" + "="*50)
    print("🤖 数据已准备完毕！现在你可以向 AI 提问了。")
    print("💡 提示：在实际应用中，这里会调用 OpenAI 或 Claude 的 API。")
    print("💡 目前为了演示，我会把你要发给 AI 的 Prompt 打印出来。")
    print("="*50 + "\n")
    
    while True:
        user_question = input("\n🧑 你想问什么？(输入 'q' 退出): ")
        if user_question.lower() == 'q':
            break
            
        # 构建给大模型的 Prompt
        prompt = f"""你是一个专业的数据分析师。请根据以下业务漏斗数据回答用户的问题。

【背景信息】
这是一个关于“{data_context[0]['dataset_name']}”的转化漏斗数据。
漏斗路径为：曝光 -> 请求 -> 请求成功 -> 采纳。

【原始数据】
{json.dumps(data_context, ensure_ascii=False, indent=2)}

【用户问题】
{user_question}

请用清晰、专业的语言进行解答，并指出数据中的关键趋势或异常点。
"""
        print("\n" + "-"*20 + " 发送给 AI 的内容 " + "-"*20)
        print(prompt[:500] + "...\n(数据部分已省略)...\n" + prompt[-200:])
        print("-" * 60)
        print("⏳ 正在等待 AI 回复... (这里可以接入真实的 API)")

if __name__ == "__main__":
    chat_with_data()