# -*- coding: utf-8 -*-
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OUTPUT_DIR = r"C:\Users\mz100\OneDrive\Pulpit\secert"

SHORTSYT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Shortsyt — Production Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;}
  body{background:#0f0f17;font-family:'Inter',sans-serif;color:#e2e8f0;padding:32px;}
  .header{text-align:center;margin-bottom:36px;}
  .logo{font-size:2.4rem;font-weight:900;background:linear-gradient(135deg,#f59e0b,#ef4444);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .sub{color:#64748b;font-size:1rem;margin-top:4px;}
  .live{display:inline-block;background:#ef4444;color:#fff;font-size:0.75rem;font-weight:700;border-radius:20px;padding:3px 12px;margin-left:12px;animation:none;}

  .kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px;}
  .kpi{background:#1a1a2e;border:1px solid #2d2d4e;border-radius:16px;padding:24px 20px;text-align:center;}
  .kpi .val{font-size:2.2rem;font-weight:900;color:#f59e0b;}
  .kpi .lbl{font-size:0.8rem;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;}
  .kpi .sub2{font-size:0.75rem;color:#475569;margin-top:2px;}

  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px;}
  .card{background:#1a1a2e;border:1px solid #2d2d4e;border-radius:16px;padding:24px;}
  .card h3{font-size:0.9rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:16px;}

  .bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
  .bar-label{font-size:0.8rem;color:#94a3b8;width:80px;text-align:right;flex-shrink:0;}
  .bar-wrap{flex:1;background:#0d0d1a;border-radius:4px;height:20px;overflow:hidden;}
  .bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:8px;}
  .bar-val{font-size:0.75rem;font-weight:700;color:#fff;}

  .top-video{display:flex;gap:12px;margin-bottom:12px;align-items:center;}
  .rank{font-size:1.2rem;font-weight:900;color:#f59e0b;width:24px;flex-shrink:0;}
  .vtitle{font-size:0.8rem;color:#cbd5e1;flex:1;line-height:1.4;}
  .vstat{font-size:0.85rem;font-weight:700;color:#34d399;flex-shrink:0;}

  .arch{background:#1a1a2e;border:1px solid #2d2d4e;border-radius:16px;padding:24px;margin-bottom:16px;}
  .arch h3{font-size:0.9rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:16px;}
  .pipeline{display:flex;align-items:center;gap:0;flex-wrap:nowrap;overflow-x:auto;}
  .step{background:#0d0d1a;border:1px solid #334155;border-radius:10px;padding:12px 16px;text-align:center;min-width:110px;}
  .step .icon{font-size:1.4rem;margin-bottom:4px;}
  .step .sname{font-size:0.7rem;color:#94a3b8;font-weight:600;}
  .step .stech{font-size:0.65rem;color:#475569;margin-top:2px;}
  .arrow{color:#f59e0b;font-size:1.2rem;padding:0 6px;flex-shrink:0;}

  .microevs{background:#0d0d1a;border-radius:10px;padding:16px;margin-top:12px;}
  .state{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
  .sdot{width:12px;height:12px;border-radius:50%;flex-shrink:0;}
  .stext{font-size:0.78rem;color:#94a3b8;}
  .sbold{color:#e2e8f0;font-weight:700;}

  .footer{text-align:center;color:#334155;font-size:0.75rem;margin-top:20px;}
</style>
</head>
<body>
<div class="header">
  <div class="logo">🧠 Shortsyt <span style="font-size:1rem;opacity:.5">by BATTLEMETAL</span></div>
  <div class="sub">Autonomous AI YouTube Shorts Pipeline — Dark Mindset Channel <span class="live">LIVE</span></div>
</div>

<div class="kpi-grid">
  <div class="kpi">
    <div class="val">95</div>
    <div class="lbl">Videos Published</div>
    <div class="sub2">2/day · autonomous</div>
  </div>
  <div class="kpi">
    <div class="val">18,049</div>
    <div class="lbl">Total Views</div>
    <div class="sub2">May 5 2026 · verified API</div>
  </div>
  <div class="kpi">
    <div class="val">$0</div>
    <div class="lbl">Cost / Video</div>
    <div class="sub2">100% local LLM — no API</div>
  </div>
  <div class="kpi">
    <div class="val">0</div>
    <div class="lbl">Human Interventions</div>
    <div class="sub2">Task Scheduler · 58+ days</div>
  </div>
</div>

<div class="grid2">
  <div class="card">
    <h3>Top 5 Videos (real API data)</h3>
    <div class="top-video">
      <div class="rank">#1</div>
      <div class="vtitle">Have you ever felt dominated by another person's body language? 📸✨</div>
      <div class="vstat">1,252 views</div>
    </div>
    <div class="top-video">
      <div class="rank">#2</div>
      <div class="vtitle">Can you spot the dark psychology body language cues that command respect?</div>
      <div class="vstat">1,181 views</div>
    </div>
    <div class="top-video">
      <div class="rank">#3</div>
      <div class="vtitle">Have you noticed how some people seem to effortlessly command respect?</div>
      <div class="vstat">1,050 views</div>
    </div>
    <div class="top-video">
      <div class="rank">#4</div>
      <div class="vtitle">Can You Spot the Dark Psychology Body Language Cues?</div>
      <div class="vstat">982 views</div>
    </div>
    <div class="top-video">
      <div class="rank">#5</div>
      <div class="vtitle">Why Asking Someone for a Favor Makes Them... 🧠</div>
      <div class="vstat">979 views</div>
    </div>
  </div>

  <div class="card">
    <h3>Performance by Duration (ML insight)</h3>
    <div class="bar-row">
      <div class="bar-label">0–10s</div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:7%;background:#ef4444;">
          <span class="bar-val">85 avg</span>
        </div>
      </div>
    </div>
    <div class="bar-row">
      <div class="bar-label">11–20s</div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:100%;background:linear-gradient(90deg,#f59e0b,#34d399);">
          <span class="bar-val">208 avg ✓ BEST</span>
        </div>
      </div>
    </div>
    <div class="bar-row">
      <div class="bar-label">21–30s</div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:93%;background:#64748b;">
          <span class="bar-val">193 avg</span>
        </div>
      </div>
    </div>
    <div class="bar-row">
      <div class="bar-label">31–60s</div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:3%;background:#ef4444;">
          <span class="bar-val">6 avg</span>
        </div>
      </div>
    </div>
    <br>
    <h3>Title Format A/B Test</h3>
    <div class="bar-row">
      <div class="bar-label">QUESTION</div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:100%;background:linear-gradient(90deg,#6366f1,#a78bfa);">
          <span class="bar-val">224 avg · 54 videos</span>
        </div>
      </div>
    </div>
    <div class="bar-row">
      <div class="bar-label">STATEMENT</div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:80%;background:#475569;">
          <span class="bar-val">179 avg · 31 videos</span>
        </div>
      </div>
    </div>
    <div class="bar-row">
      <div class="bar-label">[PREFIX]</div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:19%;background:#ef4444;">
          <span class="bar-val">42 avg — BANNED</span>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="arch">
  <h3>Pipeline Architecture — 6 Autonomous Stages</h3>
  <div class="pipeline">
    <div class="step"><div class="icon">🧠</div><div class="sname">Script Gen</div><div class="stech">Qwen 2.5 7B NF4</div></div>
    <div class="arrow">→</div>
    <div class="step"><div class="icon">🔊</div><div class="sname">TTS Audio</div><div class="stech">edge-tts</div></div>
    <div class="arrow">→</div>
    <div class="step"><div class="icon">📝</div><div class="sname">Subtitles</div><div class="stech">Whisper local</div></div>
    <div class="arrow">→</div>
    <div class="step"><div class="icon">🎬</div><div class="sname">Video Render</div><div class="stech">FFmpeg + MoviePy</div></div>
    <div class="arrow">→</div>
    <div class="step"><div class="icon">🛡️</div><div class="sname">QA Auditor</div><div class="stech">8-dim NLP check</div></div>
    <div class="arrow">→</div>
    <div class="step"><div class="icon">📡</div><div class="sname">YT Publish</div><div class="stech">Data API v3</div></div>
    <div class="arrow">→</div>
    <div class="step" style="border-color:#f59e0b;">
      <div class="icon">🔄</div>
      <div class="sname">MicroEVS</div>
      <div class="stech">Feedback Loop</div>
    </div>
  </div>
  <div class="microevs">
    <div style="font-size:0.75rem;color:#64748b;margin-bottom:10px;font-weight:700;">MicroEVS Adaptive States (self-optimizing prompt engine)</div>
    <div class="state"><div class="sdot" style="background:#34d399;"></div><div class="stext"><span class="sbold">S — Hyper-Clone (&gt;150%)</span>: Viral hit → clone exact syntax, change subject only</div></div>
    <div class="state"><div class="sdot" style="background:#f59e0b;"></div><div class="stext"><span class="sbold">A — Soft-Mutate (105–150%)</span>: Good → keep topic, change hook type</div></div>
    <div class="state"><div class="sdot" style="background:#f97316;"></div><div class="stext"><span class="sbold">B — Explore (&lt;105%)</span>: Stagnation → switch to previously successful style</div></div>
    <div class="state"><div class="sdot" style="background:#ef4444;"></div><div class="stext"><span class="sbold">F — Hard Pivot (&lt;80%)</span>: Rejection → topic banned 14 days, full reset</div></div>
  </div>
</div>

<div class="footer">
  Shortsyt · github.com/BATTLEMETAL/Shortsyt · Data: YouTube Analytics API · May 5, 2026<br>
  Stack: Python · Qwen 2.5 7B NF4 · FFmpeg · Whisper · edge-tts · sklearn · YouTube Data API v3
</div>
</body>
</html>"""

VRAM_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Synapsa — VRAM Benchmark</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;}
  body{background:#0f0f17;font-family:'Inter',sans-serif;color:#e2e8f0;padding:40px;}
  .header{text-align:center;margin-bottom:40px;}
  .logo{font-size:2rem;font-weight:900;background:linear-gradient(135deg,#8b5cf6,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .sub{color:#64748b;font-size:0.9rem;margin-top:6px;}

  .bench{background:#1a1a2e;border:1px solid #2d2d4e;border-radius:20px;padding:32px;max-width:820px;margin:0 auto;}
  .bench h3{font-size:0.85rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:24px;text-align:center;}

  .row{display:flex;align-items:center;gap:16px;margin-bottom:18px;}
  .cfg{width:220px;flex-shrink:0;}
  .cfg-name{font-size:0.85rem;font-weight:700;color:#e2e8f0;}
  .cfg-sub{font-size:0.72rem;color:#64748b;margin-top:2px;}
  .bar-area{flex:1;position:relative;}
  .bar-bg{background:#0d0d1a;border-radius:6px;height:36px;overflow:hidden;position:relative;}
  .bar-fill-v{height:100%;border-radius:6px;display:flex;align-items:center;padding-left:14px;font-size:0.85rem;font-weight:700;color:#fff;position:relative;}
  .badge{margin-left:10px;font-size:0.7rem;padding:2px 8px;border-radius:10px;font-weight:700;}
  .ok{background:#065f46;color:#34d399;}
  .fail{background:#7f1d1d;color:#fca5a5;}
  .tag{width:90px;flex-shrink:0;text-align:right;}
  .delta{font-size:0.85rem;font-weight:700;}

  .winner{border:2px solid #8b5cf6;border-radius:20px;padding:24px;text-align:center;margin-top:28px;background:#12122a;}
  .winner-title{font-size:1.4rem;font-weight:900;color:#a78bfa;}
  .winner-sub{font-size:0.9rem;color:#64748b;margin-top:6px;}
  .kpi-row{display:flex;justify-content:center;gap:40px;margin-top:20px;}
  .kpi-item .v{font-size:1.8rem;font-weight:900;color:#f59e0b;}
  .kpi-item .l{font-size:0.75rem;color:#64748b;margin-top:2px;}

  .note{color:#475569;font-size:0.72rem;text-align:center;margin-top:20px;}
</style>
</head>
<body>
<div class="header">
  <div class="logo">⚡ Synapsa VRAM Benchmark</div>
  <div class="sub">Custom Triton Patches · Qwen 2.5 7B · NVIDIA RTX 3060 12GB</div>
</div>

<div class="bench">
  <h3>VRAM Usage at Inference — RTX 3060 (12 GB limit)</h3>

  <!-- FP16 Baseline -->
  <div class="row">
    <div class="cfg">
      <div class="cfg-name">FP16 — Baseline</div>
      <div class="cfg-sub">No quantization · full precision</div>
    </div>
    <div class="bar-area">
      <div class="bar-bg">
        <div class="bar-fill-v" style="width:99%;background:#ef4444;">
          16.1 GB peak
          <span class="badge fail">❌ OOM — unusable</span>
        </div>
      </div>
    </div>
    <div class="tag"><span class="delta" style="color:#ef4444;">— baseline</span></div>
  </div>

  <!-- INT8 -->
  <div class="row">
    <div class="cfg">
      <div class="cfg-name">INT8 — 8-bit</div>
      <div class="cfg-sub">bitsandbytes standard</div>
    </div>
    <div class="bar-area">
      <div class="bar-bg">
        <div class="bar-fill-v" style="width:60%;background:#f97316;">
          9.7 GB peak
          <span class="badge ok">✅ Works</span>
        </div>
      </div>
    </div>
    <div class="tag"><span class="delta" style="color:#f97316;">−40%</span></div>
  </div>

  <!-- NF4 crashes -->
  <div class="row">
    <div class="cfg">
      <div class="cfg-name">NF4 — 4-bit</div>
      <div class="cfg-sub">Without Triton patches</div>
    </div>
    <div class="bar-area">
      <div class="bar-bg">
        <div class="bar-fill-v" style="width:40%;background:#7c3aed;">
          6.4 GB peak
          <span class="badge fail">❌ Crash — triton.cdiv</span>
        </div>
      </div>
    </div>
    <div class="tag"><span class="delta" style="color:#7c3aed;">−60%</span></div>
  </div>

  <!-- NF4 + patches (WINNER) -->
  <div class="row">
    <div class="cfg">
      <div class="cfg-name" style="color:#a78bfa;">NF4 + Triton Patches ⭐</div>
      <div class="cfg-sub">Custom Windows compat layer</div>
    </div>
    <div class="bar-area">
      <div class="bar-bg" style="border:1px solid #7c3aed;">
        <div class="bar-fill-v" style="width:38%;background:linear-gradient(90deg,#7c3aed,#06b6d4);">
          6.1 GB peak
          <span class="badge ok" style="background:#312e81;color:#a5b4fc;">✅ PRODUCTION</span>
        </div>
      </div>
    </div>
    <div class="tag"><span class="delta" style="color:#a78bfa;">−62%</span></div>
  </div>

  <div class="winner">
    <div class="winner-title">Custom Triton Patches — Production Result</div>
    <div class="winner-sub">Stable inference on RTX 3060 12 GB · Windows 11 · Zero cloud dependency</div>
    <div class="kpi-row">
      <div class="kpi-item"><div class="v">−68%</div><div class="l">VRAM at Load<br>(14.2→4.5 GB)</div></div>
      <div class="kpi-item"><div class="v">~3s</div><div class="l">Avg response<br>latency</div></div>
      <div class="kpi-item"><div class="v">100%</div><div class="l">GDPR safe<br>(offline)</div></div>
      <div class="kpi-item"><div class="v">$0</div><div class="l">API cost<br>per inference</div></div>
    </div>
  </div>
  <div class="note">
    Methodology: torch.cuda.memory_allocated() + nvidia-smi cross-validation · RTX 3060 12GB · CUDA 11.8 · bitsandbytes 0.43+<br>
    Source: github.com/BATTLEMETAL/Synapsa-Local-LLM-Agent · triton_patches/
  </div>
</div>
</body>
</html>"""

def render(html, outname):
    from playwright.sync_api import sync_playwright
    html_path = os.path.join(OUTPUT_DIR, "_tmp.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 800}, device_scale_factor=1.5)
        page.goto(f"file:///{html_path.replace(chr(92), '/')}", wait_until="networkidle")
        time.sleep(0.8)
        out = os.path.join(OUTPUT_DIR, outname)
        page.screenshot(path=out, full_page=True)
        browser.close()
    os.remove(html_path)
    sz = os.path.getsize(out)
    print(f"[OK] {outname} ({sz:,} bytes)")

if __name__ == "__main__":
    render(SHORTSYT_HTML, "21_shortsyt_dashboard.png")
    render(VRAM_HTML, "22_synapsa_vram_benchmark.png")
    print("Done.")
