# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
Portfolio Screenshots Generator - Synapsa
Generuje profesjonalne screenshoty aplikacji Streamlit do portfolio.
Wymaga: pip install playwright && playwright install chromium
"""
import os
import sys
import time
import subprocess

OUTPUT_DIR = r"C:\Users\mz100\OneDrive\Pulpit\secert"
APP_URL = "http://localhost:8503"
INVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "faktura_testowa.txt"))

os.makedirs(OUTPUT_DIR, exist_ok=True)


def check_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


def take_screenshots():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=True for CI
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=1.5,
        )
        page = context.new_page()

        print(f"[1/5] Opening {APP_URL}...")
        page.goto(APP_URL, wait_until="networkidle", timeout=15000)
        time.sleep(2)

        # Screenshot 1 — Main page (clean state)
        path1 = os.path.join(OUTPUT_DIR, "01_synapsa_main_page.png")
        page.screenshot(path=path1, full_page=True)
        print(f"  ✅ Screenshot 1: {path1}")

        # Screenshot 2 — Scroll down to show all steps
        page.evaluate("window.scrollTo(0, 200)")
        time.sleep(0.5)
        path2 = os.path.join(OUTPUT_DIR, "02_synapsa_steps_view.png")
        page.screenshot(path=path2, full_page=False)
        print(f"  ✅ Screenshot 2: {path2}")

        # Upload the test invoice file
        print(f"[2/5] Uploading test invoice: {INVOICE_PATH}...")
        file_input = page.locator("input[type='file']")
        if file_input.count() > 0:
            file_input.set_input_files(INVOICE_PATH)
            time.sleep(2)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)

            # Screenshot 3 — File uploaded
            path3 = os.path.join(OUTPUT_DIR, "03_synapsa_file_uploaded.png")
            page.screenshot(path=path3, full_page=True)
            print(f"  ✅ Screenshot 3: {path3}")

            # Click "Sprawdź fakturę" button
            print("[3/5] Clicking audit button...")
            btn = page.locator("button:has-text('Sprawdź fakturę')")
            if btn.count() > 0:
                btn.first.click()
                time.sleep(3)  # wait for results
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)

                # Screenshot 4 — Results visible
                path4 = os.path.join(OUTPUT_DIR, "04_synapsa_audit_result_top.png")
                page.screenshot(path=path4, full_page=False)
                print(f"  ✅ Screenshot 4: {path4}")

                # Scroll to results
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(0.3)
                path5 = os.path.join(OUTPUT_DIR, "05_synapsa_audit_result_details.png")
                page.screenshot(path=path5, full_page=False)
                print(f"  ✅ Screenshot 5: {path5}")

                # Full page result
                page.evaluate("window.scrollTo(0, 0)")
                path6 = os.path.join(OUTPUT_DIR, "06_synapsa_full_result.png")
                page.screenshot(path=path6, full_page=True)
                print(f"  ✅ Screenshot 6 (full page): {path6}")
            else:
                print("  ⚠️ Button not found — saving current state")
                page.screenshot(path=os.path.join(OUTPUT_DIR, "03_synapsa_state.png"), full_page=True)
        else:
            print("  ⚠️ File input not found — screenshots of main page only")

        # Screenshot — construction app
        print("[4/5] Loading construction app (app_budowlanka.py on port 8504)...")

        context.close()
        browser.close()
        print("[5/5] All screenshots saved to:", OUTPUT_DIR)
        print("\nFiles created:")
        for f in sorted(os.listdir(OUTPUT_DIR)):
            if f.endswith(".png"):
                size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
                print(f"  {f}  ({size:,} bytes)")


if __name__ == "__main__":
    if not check_playwright():
        print("Installing playwright...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"], check=True)

    take_screenshots()
