"""
Script: scripts/test_dashboard_runtime.py
Description: End-to-end runtime test of the live Streamlit dashboard.
Tests Google Careers URL analysis, verifies absence of hallucinations,
and captures verification screenshots via Chrome DevTools Protocol (CDP).
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CDP_PORT = 9222


async def send_cmd(ws, msg_dict):
    msg_id = msg_dict["id"]
    await ws.send(json.dumps(msg_dict))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            return resp


async def capture_target_screenshot(browser_ws, url: str, output_path: str, wait_secs: int = 8):
    resp = await send_cmd(browser_ws, {
        "id": 1,
        "method": "Target.createTarget",
        "params": {"url": url}
    })
    target_id = resp["result"]["targetId"]

    page_ws_url = f"ws://127.0.0.1:{CDP_PORT}/devtools/page/{target_id}"
    async with websockets.connect(page_ws_url, max_size=50 * 1024 * 1024) as page_ws:
        await send_cmd(page_ws, {"id": 10, "method": "Page.enable"})
        await send_cmd(page_ws, {
            "id": 12,
            "method": "Emulation.setDeviceMetricsOverride",
            "params": {"width": 1600, "height": 1300, "deviceScaleFactor": 1, "mobile": False}
        })

        print(f"Waiting for {url} to fetch and render...")
        for _ in range(40):
            await asyncio.sleep(1)
            resp = await send_cmd(page_ws, {
                "id": 20,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.body.innerText"}
            })
            body_text = resp["result"]["result"]["value"]
            if "Extracting structured job requirements" not in body_text and len(body_text) > 500:
                print("Page completed rendering!")
                break

        resp = await send_cmd(page_ws, {
            "id": 30,
            "method": "Page.captureScreenshot",
            "params": {"format": "png"}
        })
        img_bytes = base64.b64decode(resp["result"]["data"])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        print(f"Saved: {output_path} ({len(img_bytes)/1024:.1f} KB)")

        await send_cmd(browser_ws, {
            "id": 99,
            "method": "Target.closeTarget",
            "params": {"targetId": target_id}
        })

        return body_text


async def run_cdp_tests():
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
            print("Failed to connect to Chrome CDP.")
            return False

        print(f"Connected to Chrome CDP at {ws_url}")
        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as browser_ws:
            # 1. Capture Google Careers homepage analysis (Live fetch via Streamlit)
            google_url = "http://localhost:8501/?page=company_intelligence&target_url=https://careers.google.com/?utm_source=chatgpt.com&auto_analyze=true"
            output_google = os.path.abspath(os.path.join("reports", "screenshots", "dashboard_company_intelligence_google_insufficient.png"))
            body_google = await capture_target_screenshot(browser_ws, google_url, output_google, wait_secs=10)

            # Verification assertions
            if "Insufficient job requirement data" in body_google:
                print("✅ PASSED: 'Insufficient job requirement data' banner displayed correctly!")
            else:
                print("❌ FAILED: Banner missing from body text.")
                return False

            if "Google" in body_google:
                print("✅ PASSED: Company name 'Google' preserved correctly!")
            else:
                print("❌ FAILED: Company name 'Google' missing.")
                return False

            forbidden = ["Advanced System Design", "Production Optimization", "Cloud Deployment"]
            for f in forbidden:
                if f in body_google:
                    print(f"❌ FAILED: Hallucinated skill found: {f}")
                    return False
            print("✅ PASSED: Zero hallucinated skills found in Google Careers result!")

            # 2. Capture clean base Company Intelligence page
            base_url = "http://localhost:8501/?page=company_intelligence"
            output_base = os.path.abspath(os.path.join("reports", "screenshots", "dashboard_company_intelligence.png"))
            await capture_target_screenshot(browser_ws, base_url, output_base, wait_secs=6)

        return True

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()


def main():
    print("Launching clean Streamlit server for runtime verification...")
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
            print("Streamlit server failed to start.")
            return False

        print("Streamlit server is alive! Running CDP runtime verification...")
        success = asyncio.run(run_cdp_tests())
        return success

    finally:
        print("Cleaning up Streamlit server...")
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
    ok = main()
    sys.exit(0 if ok else 1)
