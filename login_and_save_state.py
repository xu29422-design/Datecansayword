from playwright.sync_api import sync_playwright
import time

TARGET_URL = "https://kingsight.ksord.com/index/overview?id=OVdXOXZEQ2VwcllJdElSWlhUak0rUT09&folderId=3128&overviewType=all"
STATE_FILE = "state.json"

def run():
    print("🚀 启动浏览器，请在弹出的窗口中完成登录...")
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 访问目标网页
        page.goto(TARGET_URL)
        
        print("⏳ 请在浏览器中输入账号密码进行登录。")
        print("👉 登录成功并看到数据看板后，请回到终端按 Enter 键继续...")
        
        # 等待用户手动在终端确认
        input()
        
        # 保存所有的 Cookie 和 LocalStorage 到 state.json 文件中
        context.storage_state(path=STATE_FILE)
        print(f"✅ 登录状态已成功保存到 {STATE_FILE}！")
        
        browser.close()

if __name__ == "__main__":
    run()
