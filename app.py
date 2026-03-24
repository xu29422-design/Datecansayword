import streamlit as st
import json
import os
import subprocess
from github_storage import GitHubStorage
from headless_scraper import run_scraper
from data_manager import process_and_save_to_github
from openai import OpenAI

@st.cache_resource
def install_playwright():
    """Install Playwright browsers on first run (useful for Streamlit Cloud)"""
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("Playwright chromium installed successfully.")
    except Exception as e:
        print(f"Failed to install Playwright: {e}")

install_playwright()

st.set_page_config(page_title="数据智能体", page_icon="🤖", layout="wide")

# ================= 核心配置区 =================
# 这里配置您的 GitHub 仓库信息
# 强烈建议：将 GITHUB_TOKEN 放在 Streamlit Cloud 的 Secrets 中，或者本地的环境变量中，不要硬编码在代码里！
GITHUB_REPO = "xu29422-design/Datecansayword" # 替换为您的 GitHub 仓库名
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "") # 从环境变量获取 Token
# ==========================================

# Initialize session state for config
if 'config' not in st.session_state:
    st.session_state.config = {
        "target_url": "",
        "cookie_json": "",
        "llm_api_key": "",
        "llm_base_url": "https://api.deepseek.com/v1",
        "llm_model": "deepseek-chat"
    }

if 'messages' not in st.session_state:
    st.session_state.messages = []

def load_local_config():
    try:
        with open("local_config.json", "r") as f:
            local_config = json.load(f)
            st.session_state.config.update(local_config)
    except FileNotFoundError:
        pass

def save_local_config():
    with open("local_config.json", "w") as f:
        json.dump(st.session_state.config, f, indent=2)

# Load local config on startup
if 'config_loaded' not in st.session_state:
    load_local_config()
    st.session_state.config_loaded = True

def settings_page():
    st.title("⚙️ 系统配置")
    
    st.header("1. 爬虫配置")
    target_url = st.text_input("目标爬取 URL", value=st.session_state.config.get("target_url", ""))
    cookie_json = st.text_area("Cookie JSON (从浏览器导出)", value=st.session_state.config.get("cookie_json", ""), height=150)
    
    st.header("2. 大模型 (LLM) 配置")
    llm_api_key = st.text_input("大模型 API Key", value=st.session_state.config.get("llm_api_key", ""), type="password")
    llm_base_url = st.text_input("大模型 Base URL", value=st.session_state.config.get("llm_base_url", "https://api.deepseek.com/v1"))
    llm_model = st.text_input("模型名称", value=st.session_state.config.get("llm_model", "deepseek-chat"))
    
    if st.button("保存配置"):
        st.session_state.config.update({
            "target_url": target_url,
            "cookie_json": cookie_json,
            "llm_api_key": llm_api_key,
            "llm_base_url": llm_base_url,
            "llm_model": llm_model
        })
        save_local_config()
        
        # 同步配置到 GitHub
        if GITHUB_TOKEN and GITHUB_REPO and GITHUB_REPO != "your-username/your-repo-name":
            try:
                storage = GitHubStorage(GITHUB_TOKEN, GITHUB_REPO)
                github_config = {
                    "target_url": target_url,
                    "cookie_json": cookie_json,
                    "llm_base_url": llm_base_url,
                    "llm_model": llm_model
                }
                storage.write_json("config/settings.json", github_config, "更新系统配置")
                st.success("配置已保存到本地并同步至 GitHub！")
            except Exception as e:
                st.error(f"同步至 GitHub 失败: {e}")
        else:
            st.warning("配置已保存到本地。由于未配置有效的 GitHub 仓库或 Token，未同步至云端。")

def dashboard_page():
    st.title("📊 数据看板 & 智能助手")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("操作面板")
        if st.button("🔄 立即触发数据同步"):
            if not GITHUB_TOKEN or GITHUB_REPO == "your-username/your-repo-name":
                st.error("请先在代码中配置 GITHUB_REPO 和 GITHUB_TOKEN环境变量。")
                return
                
            with st.spinner("正在爬取数据..."):
                try:
                    target_url = st.session_state.config.get("target_url")
                    cookie_json = st.session_state.config.get("cookie_json")
                    
                    if not all([target_url, cookie_json]):
                        st.error("请先在设置页面配置目标 URL 和 Cookie JSON。")
                    else:
                        intercepted_data = run_scraper(target_url, cookie_json)
                        if intercepted_data:
                            storage = GitHubStorage(GITHUB_TOKEN, GITHUB_REPO)
                            success = process_and_save_to_github(storage, intercepted_data)
                            if success:
                                st.success("数据已成功同步至 GitHub！")
                            else:
                                st.warning("未找到有效的漏斗数据进行同步。")
                        else:
                            st.warning("爬取过程中未拦截到任何数据。")
                except Exception as e:
                    st.error(f"同步失败: {e}")

    with col2:
        st.subheader("💬 与您的数据对话")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # Chat input
        if prompt := st.chat_input("问我任何关于数据的问题..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                if not GITHUB_TOKEN or GITHUB_REPO == "your-username/your-repo-name":
                    message_placeholder.markdown("⚠️ 请先在代码中配置 GITHUB_REPO 和 GITHUB_TOKEN环境变量。")
                    return
                    
                try:
                    # Fetch latest data from GitHub
                    llm_api_key = st.session_state.config.get("llm_api_key")
                    llm_base_url = st.session_state.config.get("llm_base_url")
                    llm_model = st.session_state.config.get("llm_model")
                    
                    if not llm_api_key:
                        message_placeholder.markdown("⚠️ 请先在设置页面配置大模型 API Key。")
                    else:
                        storage = GitHubStorage(GITHUB_TOKEN, GITHUB_REPO)
                        data = storage.read_json("data/funnel_data.json")
                        
                        if not data:
                            message_placeholder.markdown("⚠️ 在 GitHub 中未找到数据。请先点击左侧的“触发数据同步”。")
                        else:
                            # Compress data for prompt
                            # Keep only essential fields to save tokens
                            compressed_data = []
                            for row in data:
                                compressed_row = {k: v for k, v in row.items() if k in ['统计时间', '端', '产品', '曝光 uv', '请求uv', '请求成功uv', '采纳 uv', '请求率', '请求成功率', '采纳率']}
                                compressed_data.append(compressed_row)
                                
                            system_prompt = f"""你是一个专业的数据分析师。请根据以下业务漏斗数据回答用户的问题。
                            
                            【数据上下文】:
                            {json.dumps(compressed_data, ensure_ascii=False)}
                            
                            请用清晰、专业的中文进行解答。如果涉及到计算转化率等，请简要展示计算过程。
                            """
                            
                            client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)
                            
                            messages = [{"role": "system", "content": system_prompt}]
                            # Add recent chat history (last 5 messages)
                            messages.extend(st.session_state.messages[-5:])
                            
                            response = client.chat.completions.create(
                                model=llm_model,
                                messages=messages,
                                stream=True
                            )
                            
                            full_response = ""
                            for chunk in response:
                                if chunk.choices[0].delta.content is not None:
                                    full_response += chunk.choices[0].delta.content
                                    message_placeholder.markdown(full_response + "▌")
                                    
                            message_placeholder.markdown(full_response)
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                            
                except Exception as e:
                    message_placeholder.markdown(f"❌ 发生错误: {e}")

def main():
    st.sidebar.title("导航菜单")
    page = st.sidebar.radio("请选择页面", ["数据看板 & 对话", "系统配置"])
    
    if page == "系统配置":
        settings_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
