import json
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# ================= 配置区 =================
TARGET_URL = "https://kingsight.ksord.com/index/overview?id=OVdXOXZEQ2VwcllJdElSWlhUak0rUT09&folderId=3128&overviewType=all"
STATE_FILE = "state.json"
OUTPUT_IMAGE = "dashboard_screenshot.png"
OUTPUT_DATA_DIR = "chart_data"  # 存放拦截到的图表数据
DOWNLOAD_DIR = "downloads"      # 存放下载的Excel/CSV文件
# ==========================================

import os
import json
import time

def handle_response(response):
    """拦截并保存后台 API 返回的 JSON 数据"""
    # 过滤出 XHR 或 Fetch 请求，且状态码为 200 的响应
    if response.request.resource_type in ["xhr", "fetch"] and response.status == 200:
        try:
            # 尝试解析响应体为 JSON
            body = response.json()
            url = response.url
            
            # 这里可以根据实际的 API 路径进行过滤，比如只保存包含 'api' 或 'chart' 的请求
            # 如果不确定是哪个接口，可以先全部保存下来分析
            if "kingsight.ksord.com" in url:
                # 生成一个安全的文件名
                safe_name = url.split('/')[-1].split('?')[0]
                if not safe_name:
                    safe_name = "data"
                
                # 加上时间戳防止覆盖
                filename = f"{safe_name}_{int(time.time() * 1000)}.json"
                filepath = os.path.join(OUTPUT_DATA_DIR, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(body, f, ensure_ascii=False, indent=2)
                print(f"📊 成功拦截并保存数据接口: {url} -> {filename}")
        except Exception:
            # 如果响应体不是 JSON 格式，则忽略
            pass

def run():
    print("🚀 启动数据采集脚本 (阶段一)...")
    
    # 创建数据保存目录
    if not os.path.exists(OUTPUT_DATA_DIR):
        os.makedirs(OUTPUT_DATA_DIR)
    # 创建下载保存目录
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        
        # 直接使用保存的状态文件创建上下文（包含 Cookie 和 LocalStorage）
        try:
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                storage_state=STATE_FILE,
                accept_downloads=True # 允许自动下载文件
            )
            print("✅ 成功加载登录状态文件")
        except Exception as e:
            print(f"❌ 加载状态失败: {e}")
            print(f"💡 请先运行 python login_and_save_state.py 来生成 {STATE_FILE}")
            exit(1)
            
        page = context.new_page()
        
        # 2. 注入 Stealth 插件，抹除自动化特征，绕过基础反爬
        stealth_sync(page)
        
        # 监听所有的网络响应 (Response)
        page.on("response", handle_response)
        
        print(f"🌐 正在访问目标网页: {TARGET_URL}")
        try:
            # 访问网页，等待网络空闲 (networkidle)，确保动态加载的数据和图表请求完成
            page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"⚠️ 网页加载超时或出现错误，尝试继续执行截图: {e}")
        
        # 强制等待几秒，确保 Echarts/Canvas 等前端图表动画渲染完毕
        print("⏳ 等待图表渲染 (5秒)...")
        page.wait_for_timeout(5000) 
        
        # 3. 截图保存
        print(f"📸 正在截图并保存为 {OUTPUT_IMAGE}")
        # full_page=True 会滚动截取整个长页面。如果只需要首屏，可以改为 False
        page.screenshot(path=OUTPUT_IMAGE, full_page=True)
        print(f"🎉 截图完成！请查看当前目录下的 {OUTPUT_IMAGE}")
        
        # 4. 寻找并触发下载接口
        print("🔍 正在分析页面网络请求，寻找下载接口...")
        
        try:
            # 方案：先点击“下载”按钮，然后等待页面上出现 .xlsx 或 .csv 的链接，再点击那个链接
            download_buttons = page.locator("text=下载").all()
            if download_buttons:
                print(f"✅ 找到 {len(download_buttons)} 个包含'下载'的按钮，尝试触发...")
                for idx, btn in enumerate(download_buttons):
                    try:
                        if btn.is_visible():
                            print(f"👉 正在点击第 {idx+1} 个下载按钮...")
                            btn.dispatch_event('click')
                            
                            # 等待页面上出现包含 .xlsx 或 .csv 的链接（根据截图，它会显示进度和文件名）
                            print("⏳ 等待后端生成文件并出现下载链接...")
                            
                            # 使用 XPath 或更宽泛的文本匹配来寻找生成的文件链接
                            # 有时候文本节点被拆分了，直接用 text=/.xlsx/ 可能匹配不到
                            file_link = page.locator("a:has-text('.xlsx'), a:has-text('.csv'), span:has-text('.xlsx'), span:has-text('.csv')").first
                            
                            try:
                                # 等待元素可见，最多等 15 秒
                                file_link.wait_for(state="visible", timeout=15000)
                                
                                if file_link.is_visible():
                                    print(f"✅ 找到生成好的文件链接: {file_link.inner_text()}，准备点击下载...")
                                    
                                    # 监听真实的下载事件
                                    with page.expect_download(timeout=30000) as download_info:
                                        # 有些链接可能被覆盖，使用 JS 点击更稳妥
                                        file_link.evaluate("node => node.click()")
                                    
                                    download = download_info.value
                                    suggested_filename = download.suggested_filename
                                    download_path = os.path.join(DOWNLOAD_DIR, suggested_filename)
                                    download.save_as(download_path)
                                    print(f"🎉 成功保存文件: {download_path}")
                                    break # 成功下载一个就退出循环
                            except Exception as wait_e:
                                print(f"⚠️ 等待文件链接超时或未找到: {wait_e}")
                    except Exception as e:
                        print(f"⚠️ 点击第 {idx+1} 个按钮时发生错误: {e}")
            else:
                print("⚠️ 未找到明显的下载按钮。")
                
        except Exception as e:
            print(f"❌ 触发下载时发生错误: {e}")
        
        # 停留几秒确保下载完成
        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    run()
