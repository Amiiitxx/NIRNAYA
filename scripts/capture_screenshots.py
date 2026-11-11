"""
Script: scripts/capture_screenshots.py
Description: Captures a high-resolution screenshot of the NIRNAYA dashboard
overview page using Chrome DevTools Protocol (CDP) to guarantee complete DOM
rendering and eliminate empty/loading artifacts.
"""

import subprocess
import time
import os
import sys
import json
import urllib.request
import asyncio
import base64
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CDP_PORT = 9222
SCREENSHOT_PATH = os.path.abspath(os.path.join("reports", "screenshots", "dashboard_overview.png"))


async def capture_page_screenshot(browser_ws, url: str, output_path: str, scroll_to_bottom: bool = False):
    # Create target page
    await browser_ws.send(json.dumps({
        "id": 1,
        "method": "Target.createTarget",
        "params": {"url": url}
    }))
    resp = json.loads(await browser_ws.recv())
    target_id = resp["result"]["targetId"]

    page_ws_url = f"ws://127.0.0.1:{CDP_PORT}/devtools/page/{target_id}"
    async with websockets.connect(page_ws_url, max_size=50*1024*1024) as page_ws:
        await page_ws.send(json.dumps({"id": 10, "method": "Page.enable"}))
        await page_ws.recv()

        viewport_height = 2200 if scroll_to_bottom else 1050
        await page_ws.send(json.dumps({
            "id": 12,
            "method": "Emulation.setDeviceMetricsOverride",
            "params": {
                "width": 1600,
                "height": viewport_height,
                "deviceScaleFactor": 1,
                "mobile": False,
            }
        }))
        await page_ws.recv()

        print(f"Waiting 7 seconds for {url} to render...")
        await asyncio.sleep(7)

        if scroll_to_bottom:
            print("Scrolling stAppViewContainer to bottom to capture creator section...")
            await page_ws.send(json.dumps({
                "id": 15,
                "method": "Runtime.evaluate",
                "params": {"expression": """
                    const scroller = document.querySelector('[data-testid="stAppViewContainer"]') || 
                                     document.querySelector('section.main') || 
                                     document.documentElement;
                    if (scroller) {
                        scroller.scrollTop = scroller.scrollHeight;
                    }
                    const creatorCard = document.querySelector('h2');
                    window.scrollTo(0, 99999);
                """}
            }))
            await page_ws.recv()
            await asyncio.sleep(2)

        print(f"Capturing screenshot to {output_path}...")
        await page_ws.send(json.dumps({
            "id": 20,
            "method": "Page.captureScreenshot",
            "params": {"format": "png"}
        }))

        while True:
            msg = json.loads(await page_ws.recv())
            if msg.get("id") == 20:
                img_bytes = base64.b64decode(msg["result"]["data"])
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                print(f"Saved: {output_path} ({len(img_bytes)/1024:.1f} KB)")
                break

    # Close target
    await browser_ws.send(json.dumps({
        "id": 99,
        "method": "Target.closeTarget",
        "params": {"targetId": target_id}
    }))
    await browser_ws.recv()


async def capture_cdp_screenshot():
    # 1. Start Chrome headless with remote debugging enabled
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={CDP_PORT}",
        "--disable-gpu",
        "--no-first-run",
        "--hide-scrollbars",
        "--window-size=1600,1200",
        "about:blank",
    ])

    try:
        ws_url = None
        for _ in range(30):
            await asyncio.sleep(0.5)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=1) as resp:
                    data = json.loads(resp.read().decode())
                    ws_url = data.get("webSocketDebuggerUrl")
                    if ws_url:
                        break
            except Exception:
                pass

        if not ws_url:
            print("Failed to obtain Chrome CDP WebSocket URL.")
            return False

        print(f"Connected to Chrome DevTools Protocol at {ws_url}")
        async with websockets.connect(ws_url, max_size=50*1024*1024) as browser_ws:
            # 1. Overview Page
            await capture_page_screenshot(
                browser_ws,
                "http://localhost:8501",
                SCREENSHOT_PATH,
            )

            # 2. Company Intelligence Page
            company_screenshot_path = os.path.abspath(os.path.join("reports", "screenshots", "dashboard_company_intelligence.png"))
            await capture_page_screenshot(
                browser_ws,
                "http://localhost:8501/?page=company_intelligence",
                company_screenshot_path,
            )

            # 3. About Page with Creator Section
            about_screenshot_path = os.path.abspath(os.path.join("reports", "screenshots", "dashboard_about.png"))
            await capture_page_screenshot(
                browser_ws,
                "http://localhost:8501/?page=about",
                about_screenshot_path,
                scroll_to_bottom=True,
            )

        return True

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()


def main():
    print("Starting Streamlit server on port 8501...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    st_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.headless", "true", "--server.port", "8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        # Wait for Streamlit server health check
        server_ready = False
        for i in range(30):
            time.sleep(1)
            try:
                with urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=1) as res:
                    if res.status == 200:
                        server_ready = True
                        break
            except Exception:
                pass
            print(f"Waiting for Streamlit server... ({i+1}s)")

        if not server_ready:
            print("Streamlit server failed to start within 30 seconds.")
            return

        print("Streamlit server is alive! Triggering CDP screenshot capture...")
        asyncio.run(capture_cdp_screenshot())

    finally:
        print("Terminating Streamlit server...")
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(st_proc.pid)], capture_output=True)
        except Exception:
            pass
        st_proc.terminate()
        try:
            st_proc.wait(timeout=3)
        except Exception:
            st_proc.kill()
        print("Streamlit server terminated cleanly.")


if __name__ == "__main__":
    main()
