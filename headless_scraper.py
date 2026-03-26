import json
import time
from playwright.sync_api import sync_playwright

try:
    from playwright_stealth import stealth_sync
    HAS_STEALTH = True
except ImportError as e:
    print(f"Warning: playwright_stealth could not be imported: {e}")
    HAS_STEALTH = False

def run_scraper(target_url, cookie_json_str):
    """
    Run the scraper headlessly and return intercepted JSON data.
    """
    print("🚀 Starting headless scraper...")
    
    intercepted_data = []

    def handle_response(response):
        if response.request.resource_type in ["xhr", "fetch"] and response.status == 200:
            try:
                body = response.json()
                url = response.url
                if "kingsight.ksord.com" in url: # Or make this configurable
                    intercepted_data.append({
                        "url": url,
                        "data": body
                    })
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        try:
            # Parse the cookie JSON string
            cookies = json.loads(cookie_json_str) if cookie_json_str else []
            
            # Clean up cookies for Playwright
            valid_samesite = ["Strict", "Lax", "None"]
            for cookie in cookies:
                if "sameSite" in cookie:
                    if cookie["sameSite"] not in valid_samesite:
                        cookie["sameSite"] = "None"
                        cookie["secure"] = True
                        
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            if cookies:
                context.add_cookies(cookies)
                
            page = context.new_page()
            if HAS_STEALTH:
                stealth_sync(page)
            page.on("response", handle_response)
            
            print(f"🌐 Visiting target URL: {target_url}")
            page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # Wait for charts/data to load
            page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"❌ Scraper error: {e}")
        finally:
            browser.close()
            
    return intercepted_data
