import os
import json
import pandas as pd
import sys
import io

# 强制设置标准输出编码为 utf-8，解决 Windows 终端打印 emoji 报错的问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = "chart_data"
OUTPUT_DIR = "downloads"

def json_to_excel():
    print("🚀 开始将 JSON 数据转换为 Excel...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 遍历 chart_data 目录下的所有 json 文件
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(DATA_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 检查 JSON 结构是否符合预期（包含 list 和 columns）
            if not isinstance(data, dict) or "list" not in data or "columns" not in data:
                continue
                
            records = data["list"]
            columns_info = data["columns"]
            
            if not records:
                print(f"⚠️ {filename} 中没有数据记录，跳过。")
                continue
                
            # 构建列名映射字典：columnAsName -> columnTitle
            col_mapping = {col["columnAsName"]: col["columnTitle"] for col in columns_info}
            
            # 将数据转换为 DataFrame
            df = pd.DataFrame(records)
            
            # 重命名列
            df = df.rename(columns=col_mapping)
            
            # 过滤掉不需要的列（只保留在 columns_info 中定义过的列）
            valid_columns = [col["columnTitle"] for col in columns_info if col["columnTitle"] in df.columns]
            df = df[valid_columns]
            
            # 生成 Excel 文件名
            excel_filename = filename.replace(".json", ".xlsx")
            excel_filepath = os.path.join(OUTPUT_DIR, excel_filename)
            
            # 保存为 Excel
            df.to_excel(excel_filepath, index=False)
            print(f"✅ 成功生成 Excel: {excel_filepath}")
            
        except Exception as e:
            print(f"❌ 处理文件 {filename} 时出错: {e}")

if __name__ == "__main__":
    json_to_excel()