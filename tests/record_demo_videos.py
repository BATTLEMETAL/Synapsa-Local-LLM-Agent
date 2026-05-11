# -*- coding: utf-8 -*-
import sys, io, os, time, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
Profesjonalne nagranie demo Synapsa - pelny ekran 1920x1080.
Technika: viewport=1920x1080, --start-maximized, --kiosk
"""

OUTPUT_DIR    = r"C:\Users\mz100\OneDrive\Pulpit\secert"
INVOICE_ERROR = r"C:\Users\mz100\PycharmProjects\Synapsa\tests\faktura_testowa.txt"
INVOICE_OK    = r"C:\Users\mz100\PycharmProjects\Synapsa\tests\faktura_ok.txt"
TEMP_DIR      = os.path.join(OUTPUT_DIR, "_vid_tmp")

# Full HD
W, H = 1920, 1080


def slow_scroll(page, amount=400, steps=8, delay=0.07):
    """Plynny scroll - wyglada profesjonalnie."""
    step = amount // steps
    for _ in range(steps):
        page.evaluate(f"window.scrollBy(0, {step})")
        time.sleep(delay)


def wait_app(page, ms=2000):
    time.sleep(ms / 1000)


def record_synapsa():
    from playwright.sync_api import sync_playwright
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=== SYNAPSA — Audyt Faktur VAT ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=250,
            args=[
                "--start-maximized",
                "--disable-infobars",
                "--no-default-browser-check",
                f"--window-size={W},{H}",
                "--window-position=0,0",
            ]
        )
        context = browser.new_context(
            no_viewport=True,             # let window control size
            record_video_dir=TEMP_DIR,
            record_video_size={"width": W, "height": H},
        )
        page = context.new_page()

        # --- INTRO: Main page ---
        print("  > Loading main page...")
        page.goto("http://localhost:8503", wait_until="networkidle", timeout=20000)
        wait_app(page, 2500)

        # Scroll slowly to show step descriptions
        slow_scroll(page, amount=350, steps=10, delay=0.1)
        wait_app(page, 1200)
        slow_scroll(page, amount=-350, steps=10, delay=0.08)
        wait_app(page, 1000)

        # --- DEMO 1: Valid invoice -> GREEN result ---
        print("  > Demo 1: VALID invoice (green)...")
        file_input = page.locator("input[type='file']")
        file_input.set_input_files(INVOICE_OK)
        wait_app(page, 1800)

        # Scroll to show file name
        slow_scroll(page, amount=200, steps=6, delay=0.1)
        wait_app(page, 1000)

        # Click the big red audit button
        btn = page.locator("button[kind='primary']")
        if btn.count() > 0:
            btn.first.click()
        wait_app(page, 1500)  # let spinner appear

        # Scroll to reveal result
        slow_scroll(page, amount=500, steps=14, delay=0.09)
        wait_app(page, 3000)   # pause on green box

        # Scroll to bottom (download buttons)
        slow_scroll(page, amount=400, steps=10, delay=0.09)
        wait_app(page, 2000)

        # Scroll back to top
        slow_scroll(page, amount=-900, steps=12, delay=0.07)
        wait_app(page, 1500)

        # --- DEMO 2: Invoice with errors -> RED result ---
        print("  > Demo 2: ERROR invoice (red)...")
        page.reload(wait_until="networkidle")
        wait_app(page, 2000)

        file_input = page.locator("input[type='file']")
        file_input.set_input_files(INVOICE_ERROR)
        wait_app(page, 1500)

        slow_scroll(page, amount=200, steps=5, delay=0.1)
        wait_app(page, 800)

        btn = page.locator("button[kind='primary']")
        if btn.count() > 0:
            btn.first.click()
        wait_app(page, 1500)

        # Reveal red error box
        slow_scroll(page, amount=500, steps=14, delay=0.09)
        wait_app(page, 3000)   # pause on red error box

        slow_scroll(page, amount=400, steps=10, delay=0.09)
        wait_app(page, 2000)

        slow_scroll(page, amount=-900, steps=12, delay=0.07)
        wait_app(page, 2000)   # final pause before cut

        print("  > Saving video...")
        context.close()
        browser.close()

    _save_video(TEMP_DIR, "DEMO_synapsa_invoice_audit.webm")


def record_budowlanka():
    from playwright.sync_api import sync_playwright
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=== BUDOWLANKA — Kosztorys → Faktura ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=[
                "--start-maximized",
                "--disable-infobars",
                "--no-default-browser-check",
                f"--window-size={W},{H}",
                "--window-position=0,0",
            ]
        )
        context = browser.new_context(
            no_viewport=True,
            record_video_dir=TEMP_DIR,
            record_video_size={"width": W, "height": H},
        )
        page = context.new_page()

        # --- INTRO ---
        print("  > Loading Budowlanka...")
        page.goto("http://localhost:8504", wait_until="networkidle", timeout=20000)
        wait_app(page, 2500)

        # Show tabs
        slow_scroll(page, amount=150, steps=5, delay=0.1)
        wait_app(page, 800)
        slow_scroll(page, amount=-150, steps=5, delay=0.08)
        wait_app(page, 1000)

        # --- Type order naturally ---
        print("  > Typing order description...")
        ta = page.locator("textarea").first
        ta.click()
        wait_app(page, 500)
        ta.type(
            "Budowa ogrodzenia z klinkieru, 50 metrow biezacych, cena 300 zl za metr, termin realizacji 2 tygodnie.",
            delay=45
        )
        wait_app(page, 800)

        # Fill company field
        print("  > Filling company data...")
        inputs = page.locator("input[type='text']")
        if inputs.count() >= 1:
            inputs.nth(0).click()
            wait_app(page, 300)
            inputs.nth(0).type("Budowlanka Sp. z o.o., NIP: 123-456-78-90", delay=25)
            wait_app(page, 400)
        if inputs.count() >= 2:
            inputs.nth(1).click()
            wait_app(page, 300)
            inputs.nth(1).type("Jan Kowalski, NIP: 987-654-32-10", delay=25)
            wait_app(page, 600)

        # Pause to show filled form
        wait_app(page, 1500)

        # Click generate
        print("  > Generating invoice...")
        btn = page.locator("button[kind='primary']")
        if btn.count() > 0:
            btn.first.click()
        wait_app(page, 2000)   # spinner

        # Scroll to show result
        slow_scroll(page, amount=500, steps=14, delay=0.09)
        wait_app(page, 3000)   # pause on result

        slow_scroll(page, amount=400, steps=10, delay=0.09)
        wait_app(page, 2500)

        slow_scroll(page, amount=-900, steps=12, delay=0.07)
        wait_app(page, 2000)

        # Show other tabs quickly
        print("  > Showing assistant tab...")
        tabs = page.locator("button[data-testid='stTab']")
        if tabs.count() >= 2:
            tabs.nth(1).click()  # Asystent tab
            wait_app(page, 2000)
            tabs.nth(0).click()  # back to main
            wait_app(page, 1500)

        wait_app(page, 1500)

        print("  > Saving video...")
        context.close()
        browser.close()

    _save_video(TEMP_DIR, "DEMO_budowlanka_invoice.webm")


def _save_video(tmp_dir, name):
    videos = [f for f in os.listdir(tmp_dir) if f.endswith(".webm")]
    if videos:
        src = os.path.join(tmp_dir, videos[0])
        dst = os.path.join(OUTPUT_DIR, name)
        shutil.move(src, dst)
        sz = os.path.getsize(dst)
        print(f"  [SAVED] {name} — {sz:,} bytes ({sz//1024//1024} MB {sz//1024 % 1024} KB)")
    else:
        print("  [WARN] No video found in temp dir!")
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    print(f"Target resolution: {W}x{H} (Full HD)\n")

    # Remove old demos
    for old in ["DEMO_synapsa_invoice_audit.webm", "DEMO_budowlanka_invoice.webm"]:
        p = os.path.join(OUTPUT_DIR, old)
        if os.path.exists(p):
            os.remove(p)
            print(f"Removed old: {old}")

    print()
    record_synapsa()
    print()
    record_budowlanka()

    print("\n=== DONE ===")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.startswith("DEMO_") and f.endswith(".webm"):
            sz = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"  {f}  {sz//1024//1024}MB {sz//1024 % 1024}KB")
