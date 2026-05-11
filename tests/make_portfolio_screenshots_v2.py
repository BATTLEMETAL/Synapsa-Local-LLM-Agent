# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
Portfolio Screenshots v2 - Synapsa
Lepsze screenshoty: scroll po wyniku, oba statusy faktury (OK i BLEDY)
"""
import os
import time

OUTPUT_DIR = r"C:\Users\mz100\OneDrive\Pulpit\secert"
APP_URL = "http://localhost:8503"
INVOICE_ERROR = os.path.abspath(os.path.join(os.path.dirname(__file__), "faktura_testowa.txt"))
INVOICE_OK = os.path.abspath(os.path.join(os.path.dirname(__file__), "faktura_ok.txt"))

os.makedirs(OUTPUT_DIR, exist_ok=True)


def full_demo(page, invoice_path, prefix, label):
    print(f"\n--- [{label}] Uploading: {os.path.basename(invoice_path)} ---")
    page.goto(APP_URL, wait_until="networkidle", timeout=15000)
    time.sleep(1.5)

    # Screenshot main page
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"{prefix}_A_main.png"), full_page=True)
    print(f"  [OK] {prefix}_A_main.png")

    # Upload invoice
    file_input = page.locator("input[type='file']")
    if file_input.count() == 0:
        print("  [WARN] No file input found!")
        return

    file_input.set_input_files(invoice_path)
    time.sleep(1.5)

    # Screenshot after upload
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"{prefix}_B_uploaded.png"), full_page=True)
    print(f"  [OK] {prefix}_B_uploaded.png")

    # Click audit button
    btn = page.locator("button:has-text('Sprawdz fakture'), button:has-text('Sprawdź fakturę')")
    if btn.count() == 0:
        btn = page.locator("button[kind='primary']")
    if btn.count() > 0:
        btn.first.click()
        time.sleep(3)

    # Scroll to top then screenshot
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.5)
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"{prefix}_C_result_top.png"), full_page=False)
    print(f"  [OK] {prefix}_C_result_top.png")

    # Scroll down to see result details
    page.evaluate("window.scrollBy(0, 600)")
    time.sleep(0.5)
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"{prefix}_D_result_detail.png"), full_page=False)
    print(f"  [OK] {prefix}_D_result_detail.png")

    # Full page result
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.3)
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"{prefix}_E_full.png"), full_page=True)
    print(f"  [OK] {prefix}_E_full.png")

    # Scroll to bottom to capture download buttons
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.3)
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"{prefix}_F_bottom.png"), full_page=False)
    print(f"  [OK] {prefix}_F_bottom.png")


def budowlanka_demo(page):
    print("\n--- [BUDOWLANKA] Construction app demo ---")
    page.goto("http://localhost:8504", wait_until="networkidle", timeout=15000)
    time.sleep(2)

    # Main page
    page.screenshot(path=os.path.join(OUTPUT_DIR, "BUD_A_main.png"), full_page=True)
    print("  [OK] BUD_A_main.png")

    # Fill form
    opis = page.locator("textarea").first
    if opis.count() > 0 or page.locator("textarea").count() > 0:
        ta = page.locator("textarea").first
        ta.click()
        ta.fill("Budowa ogrodzenia z klinkieru, 50 metrow biezacych, cena 300 zl za metr, termin realizacji 2 tygodnie.")
        time.sleep(0.5)

    # Fill company
    inputs = page.locator("input[type='text']")
    if inputs.count() >= 1:
        inputs.nth(0).fill("Budowlanka Sp. z o.o., NIP: 123-456-78-90")
    if inputs.count() >= 2:
        inputs.nth(1).fill("Jan Kowalski, NIP: 987-654-32-10")
    time.sleep(0.5)

    page.screenshot(path=os.path.join(OUTPUT_DIR, "BUD_B_form_filled.png"), full_page=False)
    print("  [OK] BUD_B_form_filled.png")

    # Click generate
    btn = page.locator("button:has-text('Oblicz i wystaw fakture'), button:has-text('Oblicz i wystaw fakturę')")
    if btn.count() == 0:
        btn = page.locator("button[kind='primary']")
    if btn.count() > 0:
        btn.first.click()
        time.sleep(5)  # wait for LLM or rule engine

    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.5)
    page.screenshot(path=os.path.join(OUTPUT_DIR, "BUD_C_result.png"), full_page=True)
    print("  [OK] BUD_C_result.png")

    page.evaluate("window.scrollBy(0, 600)")
    time.sleep(0.3)
    page.screenshot(path=os.path.join(OUTPUT_DIR, "BUD_D_invoice.png"), full_page=False)
    print("  [OK] BUD_D_invoice.png")


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 860},
            device_scale_factor=1.5,
        )
        page = context.new_page()

        # Demo 1: Invoice with errors (shows red box)
        full_demo(page, INVOICE_ERROR, "ERR", "Invoice with errors")

        # Demo 2: Valid invoice (shows green box)
        full_demo(page, INVOICE_OK, "OK_", "Valid invoice")

        # Demo 3: Budowlanka construction app
        budowlanka_demo(page)

        context.close()
        browser.close()

    print("\n\n=== All screenshots saved ===")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith(".png") and (f.startswith("ERR") or f.startswith("OK_") or f.startswith("BUD")):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"  {f}  ({size:,} bytes)")


if __name__ == "__main__":
    main()
