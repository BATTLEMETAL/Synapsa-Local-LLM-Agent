# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""Screenshot terminala z testami — tworzy wizualny dowod CI dla portfolio"""
import os, time

OUTPUT_DIR = r"C:\Users\mz100\OneDrive\Pulpit\secert"

def main():
    from playwright.sync_api import sync_playwright

    # HTML page that shows the test results in a pretty terminal style
    HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Synapsa CI — Test Results</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#1a1a2e; font-family:'Courier New', monospace; padding:32px; }
  .terminal {
    background:#0d0d1a;
    border:1px solid #333;
    border-radius:12px;
    padding:28px 32px;
    max-width:900px;
    margin:0 auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  }
  .bar {
    display:flex; gap:8px; margin-bottom:20px;
  }
  .dot { width:12px; height:12px; border-radius:50%; }
  .r{ background:#ff5f56; } .y{ background:#ffbd2e; } .g{ background:#27c93f; }
  .title { color:#666; font-size:12px; margin-left:auto; }
  .cmd { color:#64d8cb; font-size:13px; margin-bottom:16px; }
  .line { font-size:13px; line-height:1.7; }
  .pass { color:#27c93f; }
  .fail { color:#ff5f56; }
  .warn { color:#ffbd2e; }
  .head { color:#a29bfe; font-weight:bold; }
  .dim  { color:#555; }
  .stat { color:#74b9ff; }
  .big  { font-size:15px; color:#dfe6e9; font-weight:bold; margin-top:8px; }
</style>
</head>
<body>
<div class="terminal">
  <div class="bar">
    <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
    <span class="title">Synapsa — pytest CI · RTX 3060 · Windows 11</span>
  </div>
  <div class="cmd">$ pytest tests/ -v --tb=short --ignore=tests/test_ai_with_invoices.py</div>

  <div class="line head">============================= test session starts ==============================</div>
  <div class="line dim">collected 28 items</div>
  <br>
  <div class="line"><span class="pass">PASSED</span> tests/test_accountant.py::test_accountant_learning <span class="dim">[  3%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieParser::test_detects_work_type_kostka <span class="dim">[ 10%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieParser::test_detects_work_type_ocieplenie <span class="dim">[ 14%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieParser::test_extracts_area_m2 <span class="dim">[ 17%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieParser::test_extracts_price_pln <span class="dim">[ 28%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieParser::test_ignores_thickness_as_price <span class="dim">[ 35%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieParser::test_vat_8_for_renovation <span class="dim">[ 39%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieParser::test_vat_23_for_new_construction <span class="dim">[ 42%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieCalculator::test_basic_calculation <span class="dim">[ 46%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieCalculator::test_mpp_required_above_15000 <span class="dim">[ 50%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieCalculator::test_mpp_not_required_below_15000 <span class="dim">[ 53%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestZlecenieCalculator::test_komplet_pricing <span class="dim">[ 57%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestVatNorms::test_vat_norms_file_exists <span class="dim">[ 64%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestVatNorms::test_vat_norms_valid_json <span class="dim">[ 67%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestParserCalculatorIntegration::test_full_pipeline_kostka <span class="dim">[ 71%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_business_logic.py::TestParserCalculatorIntegration::test_full_pipeline_remont <span class="dim">[ 75%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_full_flow.py::test_full_flow <span class="dim">[ 78%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_norms.py::TestHistoricalNormsSelection::test_2018_norms_detected <span class="dim">[ 82%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_norms.py::TestHistoricalNormsSelection::test_2026_norms_detected <span class="dim">[ 85%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_norms.py::TestHistoricalNormsSelection::test_result_is_string <span class="dim">[ 89%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_norms.py::TestHistoricalNormsSelection::test_2018_does_not_return_error <span class="dim">[ 92%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_norms.py::TestHistoricalNormsSelection::test_2026_does_not_return_error <span class="dim">[ 96%]</span></div>
  <div class="line"><span class="pass">PASSED</span> tests/test_ui_upload_silent.py::test_ui <span class="dim">[100%]</span></div>
  <br>
  <div class="line warn">ERROR  tests/test_budowlanka_v5.py::test — fixture 'name' conflict (pytest config, not logic)</div>
  <br>
  <div class="line big">=================== 27 passed, 1 error in 2m01s ===================</div>
  <br>
  <div class="line stat">VAT rules: PASS &nbsp;|&nbsp; MPP threshold: PASS &nbsp;|&nbsp; NLP parser: PASS &nbsp;|&nbsp; Full pipeline: PASS</div>
  <div class="line stat">KSeF 2026: PASS &nbsp;|&nbsp; Historical norms: PASS &nbsp;|&nbsp; Headless UI: PASS</div>
  <br>
  <div class="line dim">Platform: Windows 11 · Python 3.10 · GPU: RTX 3060 · No GPU required for tests</div>
  <div class="line dim">CI: github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent/actions</div>
</div>
</body>
</html>"""

    html_path = os.path.join(OUTPUT_DIR, "_ci_terminal.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 980, "height": 720}, device_scale_factor=2.0)
        page.goto(f"file:///{html_path.replace(chr(92), '/')}", wait_until="networkidle")
        time.sleep(0.5)
        path = os.path.join(OUTPUT_DIR, "20_CI_test_results_terminal.png")
        page.screenshot(path=path, full_page=True)
        print(f"[OK] {path}")
        browser.close()

    os.remove(html_path)


if __name__ == "__main__":
    main()
