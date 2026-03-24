# 数据看板自动化采集系统 (Phase 1)

这是自动化采集系统的第一阶段 MVP（最小可行性产品）代码。
主要功能：携带 Cookie 绕过登录，使用 Playwright Stealth 绕过基础反爬，并对动态渲染的图表看板进行全页截图。

## 1. 环境准备

请在终端中运行以下命令安装依赖库和浏览器内核：

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 所需的 Chromium 浏览器内核
playwright install chromium
```

## 2. 获取并配置 Cookie

由于目标系统需要登录，我们需要手动导出一次 Cookie 给程序使用：

1. 打开你日常使用的浏览器（如 Chrome/Edge）。
2. 正常登录目标网站 `https://kingsight.ksord.com/`。
3. 安装一个 Cookie 导出插件，例如 **EditThisCookie** 或 **Cookie-Editor**。
4. 在目标网页上点击插件，选择 **"Export" (导出为 JSON 格式)**。
5. 打开本项目中的 `cookies.json` 文件，将里面的内容**全部替换**为你刚刚复制的 JSON 数据并保存。

## 3. 运行脚本

在终端中执行以下命令：

```bash
python scraper.py
```

## 4. 预期效果

1. 脚本会自动弹出一个 Chrome 浏览器窗口。
2. 浏览器会自动携带你的 Cookie 访问目标看板 URL（无需再次输入密码）。
3. 脚本会等待网页加载完毕和图表渲染完成。
4. 最终在当前目录下生成一张名为 `dashboard_screenshot.png` 的高清长截图。