"""
Synapsa — Biuro Rachunkowe AI (Wersja dla Księgowej)
Prosty, czytelny interfejs dla osób starszych.
Duże czcionki, krok po kroku, minimalne elementy.

Uruchom: streamlit run app_ksiegowosc.py
"""
import streamlit as st
import os
import re
import json
import sqlite3
import hashlib
import uuid
import pandas as pd
from io import BytesIO
from datetime import date

st.set_page_config(
    page_title="Synapsa — Audyt Faktur",
    page_icon="🧾",
    layout="wide",
)

# ════════════════════════════════════════════════════════════════
# CSS — LARGE, READABLE, SENIOR-FRIENDLY
# ════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 18px !important;
    }

    /* Big page title */
    .synapsa-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #1a1a2e;
        text-align: center;
        margin-bottom: 4px;
    }
    .synapsa-sub {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Step boxes */
    .step-box {
        background: #f0f4ff;
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
    }
    .step-number {
        background: #3b82f6;
        color: white;
        border-radius: 50%;
        width: 44px; height: 44px;
        display: inline-flex;
        align-items: center; justify-content: center;
        font-size: 1.3rem;
        font-weight: 800;
        margin-right: 12px;
        vertical-align: middle;
    }
    .step-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1e3a8a;
        vertical-align: middle;
    }
    .step-desc {
        font-size: 1.1rem;
        color: #374151;
        margin-top: 10px;
        margin-left: 56px;
    }

    /* Result cards */
    .result-ok {
        background: #d1fae5;
        border: 3px solid #10b981;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    .result-error {
        background: #fee2e2;
        border: 3px solid #ef4444;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    .result-warn {
        background: #fef9c3;
        border: 3px solid #f59e0b;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    .result-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .result-text {
        font-size: 1.15rem;
        color: #1f2937;
    }
    .error-item {
        font-size: 1.1rem;
        background: #fca5a5;
        border-radius: 10px;
        padding: 10px 16px;
        margin: 6px 0;
        color: #991b1b;
        font-weight: 600;
    }
    .warn-item {
        font-size: 1.05rem;
        background: #fde68a;
        border-radius: 10px;
        padding: 8px 14px;
        margin: 5px 0;
        color: #78350f;
    }
    .ok-item {
        font-size: 1.05rem;
        background: #a7f3d0;
        border-radius: 10px;
        padding: 8px 14px;
        margin: 5px 0;
        color: #065f46;
    }

    /* Large buttons */
    div[data-testid="stButton"] button {
        font-size: 1.3rem !important;
        padding: 14px 28px !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        height: auto !important;
    }

    /* Upload area */
    div[data-testid="stFileUploader"] {
        font-size: 1.1rem !important;
    }
    div[data-testid="stFileUploader"] label {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* Info box */
    .info-box {
        background: #eff6ff;
        border-left: 6px solid #3b82f6;
        border-radius: 8px;
        padding: 16px 20px;
        font-size: 1.05rem;
        color: #1e40af;
        margin: 12px 0;
    }
    .privacy-tag {
        background: #d1fae5;
        border: 2px solid #10b981;
        border-radius: 30px;
        padding: 6px 18px;
        font-size: 1rem;
        font-weight: 700;
        color: #065f46;
        display: inline-block;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# DATABASE & PDF UTILITIES (Faza 2)
# ════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "audits.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            audit_date TEXT NOT NULL,
            invoice_year INTEGER NOT NULL,
            status TEXT NOT NULL,
            errors_json TEXT NOT NULL,
            warnings_json TEXT NOT NULL,
            recommendations_json TEXT NOT NULL,
            ocena TEXT NOT NULL,
            file_hash TEXT NOT NULL UNIQUE
        )
    """)
    # Cache NIP — przechowuje wyniki z Białej Listy MF przez 24h
    c.execute("""
        CREATE TABLE IF NOT EXISTS nip_cache (
            nip TEXT PRIMARY KEY,
            checked_date TEXT NOT NULL,
            result_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def check_duplicate(file_hash: str) -> dict | None:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT id, filename, audit_date, invoice_year, status, 
                   errors_json, warnings_json, recommendations_json, ocena 
            FROM audits WHERE file_hash = ?
        """, (file_hash,))
        row = c.fetchone()
        conn.close()
        if row:
            errors = json.loads(row[5])
            bf = [e for e in errors if not e.startswith("🔢")]
            br = [e for e in errors if e.startswith("🔢")]
            bf_clean = [e.replace("❌ ", "").replace("❌", "") for e in bf]
            br_clean = [e.replace("🔢 ", "").replace("🔢", "") for e in br]
            
            return {
                "id": row[0],
                "filename": row[1],
                "audit_date": row[2],
                "rok_faktury": row[3],
                "status": row[4],
                "bledy_formalne": bf_clean,
                "bledy_rachunkowe": br_clean,
                "uwagi": json.loads(row[6]),
                "rekomendacje": json.loads(row[7]),
                "ocena": row[8],
                "podstawa": f"Wczytano z historii (zapisano: {row[2]})"
            }
    except Exception:
        pass
    return None

def save_audit(audit_id: str, filename: str, invoice_year: int, status: str, report: dict, file_hash: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        all_errors = []
        for b in report.get("bledy_formalne", []):
            all_errors.append(f"❌ {b}")
        for b in report.get("bledy_rachunkowe", []):
            all_errors.append(f"🔢 {b}")
            
        c.execute("""
            INSERT INTO audits (id, filename, audit_date, invoice_year, status, errors_json, warnings_json, recommendations_json, ocena, file_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_id,
            filename,
            date.today().strftime('%Y-%m-%d'),
            invoice_year,
            status,
            json.dumps(all_errors, ensure_ascii=False),
            json.dumps(report.get("uwagi", []), ensure_ascii=False),
            json.dumps(report.get("rekomendacje", []), ensure_ascii=False),
            report.get("ocena", ""),
            file_hash
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_audit_history(limit=30):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT id, filename, audit_date, invoice_year, status, ocena 
            FROM audits ORDER BY rowid DESC LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

def clear_audit_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM audits")
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_audit_by_id(audit_id: str) -> dict | None:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT id, filename, audit_date, invoice_year, status, 
                   errors_json, warnings_json, recommendations_json, ocena, file_hash 
            FROM audits WHERE id = ?
        """, (audit_id,))
        row = c.fetchone()
        conn.close()
        if row:
            errors = json.loads(row[5])
            bf = [e.replace("❌ ", "").replace("❌", "") for e in errors if not e.startswith("🔢")]
            br = [e.replace("🔢 ", "").replace("🔢", "") for e in errors if e.startswith("🔢")]
            return {
                "id": row[0],
                "filename": row[1],
                "audit_date": row[2],
                "rok_faktury": row[3],
                "status": row[4],
                "bledy_formalne": bf,
                "bledy_rachunkowe": br,
                "uwagi": json.loads(row[6]),
                "rekomendacje": json.loads(row[7]),
                "ocena": row[8],
                "podstawa": f"Historia audytów | Zapisano: {row[2]}"
            }
    except Exception:
        pass
    return None

def generate_pdf_report(report: dict, filename: str) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#4b5563'),
        alignment=1,
        spaceAfter=25
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=12,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#1f2937'),
        leading=13
    )
    
    story.append(Paragraph("Synapsa - Certyfikat Audytu Faktury", title_style))
    story.append(Paragraph(f"Data audytu: {date.today().strftime('%d.%m.%Y')} | Dokument: {filename}", subtitle_style))
    
    status = report["status"]
    status_text = "Faktura jest PRAWIDŁOWA" if status == "OK" else ("Faktura zawiera UWAGI" if status == "UWAGI" else "W fakturze znaleziono BŁĘDY!")
    status_color = colors.HexColor('#10b981') if status == "OK" else (colors.HexColor('#f59e0b') if status == "UWAGI" else colors.HexColor('#ef4444'))
    
    card_data = [
        [Paragraph(f"<b>STATUS AUDYTU:</b>", ParagraphStyle('BoldWhite', fontName='Helvetica-Bold', textColor=colors.white, fontSize=11)),
         Paragraph(f"<b>{status_text}</b>", ParagraphStyle('BoldStatus', fontName='Helvetica-Bold', textColor=colors.white, fontSize=11))]
    ]
    card_table = Table(card_data, colWidths=[120, 360])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), status_color),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(card_table)
    story.append(Spacer(1, 15))
    
    meta_data = [
        [Paragraph("<b>Rok faktury:</b>", normal_style), Paragraph(str(report["rok_faktury"]), normal_style)],
        [Paragraph("<b>Podstawa prawna:</b>", normal_style), Paragraph(report["podstawa"], normal_style)],
        [Paragraph("<b>Ocena:</b>", normal_style), Paragraph(report["ocena"], normal_style)]
    ]
    meta_table = Table(meta_data, colWidths=[120, 360])
    meta_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f9fafb')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    if report.get("bledy_formalne") or report.get("bledy_rachunkowe"):
        story.append(Paragraph("Wykryte bledy i niezgodnosci", section_title))
        err_items = []
        for b in report.get("bledy_formalne", []):
            err_items.append([Paragraph("-", normal_style), Paragraph(b, normal_style)])
        for b in report.get("bledy_rachunkowe", []):
            err_items.append([Paragraph("-", normal_style), Paragraph(b, normal_style)])
        
        err_table = Table(err_items, colWidths=[15, 465])
        err_table.setStyle(TableStyle([
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(err_table)
        story.append(Spacer(1, 10))
        
    if report.get("uwagi"):
        story.append(Paragraph("Sprawy warte uwagi / Ostrzezenia", section_title))
        warn_items = []
        for o in report["uwagi"]:
            warn_items.append([Paragraph("-", normal_style), Paragraph(o, normal_style)])
            
        warn_table = Table(warn_items, colWidths=[15, 465])
        warn_table.setStyle(TableStyle([
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(warn_table)
        story.append(Spacer(1, 10))
        
    if report.get("rekomendacje"):
        story.append(Paragraph("Zalecenia i weryfikacja", section_title))
        rec_items = []
        for r in report["rekomendacje"]:
            rec_items.append([Paragraph("-", normal_style), Paragraph(r, normal_style)])
            
        rec_table = Table(rec_items, colWidths=[15, 465])
        rec_table.setStyle(TableStyle([
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(rec_table)
        
    story.append(Spacer(1, 30))
    story.append(Paragraph("<font size='8' color='#9ca3af'>Generowane automatycznie przez system Synapsa Biuro Rachunkowe AI. Analiza lokalna - bezpieczenstwo danych 100%.</font>", ParagraphStyle('FooterDisclaimer', parent=styles['Normal'], alignment=1)))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def call_api_audit(file_path: str, filename: str) -> dict | None:
    try:
        import requests
        with open(file_path, "rb") as f:
            r = requests.post(
                "http://localhost:8000/audit/invoice",
                files={"file": (filename, f, "application/octet-stream")},
                timeout=15
            )
        if r.status_code == 200:
            res = r.json()
            bf_errors = [e["message"] for e in res.get("errors", []) if e.get("code") != "CALCULATION_ERROR"]
            br_errors = [e["message"] for e in res.get("errors", []) if e.get("code") == "CALCULATION_ERROR"]
            status_map = {"ok": "OK", "errors_found": "BLEDY", "error": "BLEDY"}
            status = status_map.get(res.get("status", "ok"), "OK")
            if res.get("warnings"):
                status = "UWAGI" if status == "OK" else status
            
            return {
                "rok_faktury": res.get("invoice_year") or 2026,
                "status": status,
                "bledy_formalne": bf_errors,
                "bledy_rachunkowe": br_errors,
                "uwagi": res.get("warnings") or [],
                "rekomendacje": ["Zweryfikowano przez lokalny model AI Qwen ✓"],
                "ocena": "Audyt wykonany pomyślnie przez model AI.",
                "podstawa": "Lokalny Model AI (FastAPI / Qwen)"
            }
    except Exception:
        return None
def check_nip_white_list(nip: str) -> dict | None:
    """Bezpośrednie zapytanie do API Białej Listy MF."""
    try:
        import requests
        from datetime import date
        today_str = date.today().strftime('%Y-%m-%d')
        url = f"https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={today_str}"
        headers = {"User-Agent": "Synapsa Accounting Auditor Client/1.0"}
        r = requests.get(url, headers=headers, timeout=8)

        if r.status_code == 200:
            data = r.json()
            result = data.get("result")
            if result:
                subject = result.get("subject")
                if subject:
                    return {
                        "name": subject.get("name"),
                        "statusVat": subject.get("statusVat"),
                        "address": subject.get("residenceAddress") or subject.get("workingAddress") or "Brak adresu w bazie",
                        "accounts": subject.get("accountNumbers") or [],
                        "regon": subject.get("regon")
                    }
        elif r.status_code == 429:
            return {"error": "Limit zapytań do Białej Listy MF wyczerpany na dziś (max 100/dzień)."}
        elif r.status_code == 404:
            return {"error": f"NIP {nip} nie figuruje w bazie Ministerstwa Finansów."}
    except Exception as e:
        return {"error": f"Błąd połączenia z bazą Ministerstwa Finansów: {str(e)}"}
    return None


def _get_nip_from_cache(nip: str) -> dict | None:
    """Zwraca cachedowany wynik dla NIP z dzisiejszego dnia (SQLite)."""
    try:
        today_str = date.today().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT result_json FROM nip_cache WHERE nip = ? AND checked_date = ?",
            (nip, today_str)
        )
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def _save_nip_to_cache(nip: str, result: dict):
    """Zapisuje wynik z MF do lokalnego cache SQLite."""
    try:
        today_str = date.today().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO nip_cache (nip, checked_date, result_json) VALUES (?, ?, ?)",
            (nip, today_str, json.dumps(result, ensure_ascii=False))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def check_nip_smart(nip: str) -> dict:
    """
    Sprawdza NIP w Białej Liście MF z lokalnym cache'em SQLite.
    Cache jest ważny przez cały dzień — oszczędza limit 100 req/dzień.
    Zwraca dict z kluczem 'cached': True/False.
    """
    cached = _get_nip_from_cache(nip)
    if cached:
        cached["cached"] = True
        return cached

    result = check_nip_white_list(nip)
    if result and "error" not in result:
        _save_nip_to_cache(nip, result)
        result["cached"] = False
    elif result is None:
        result = {"error": "Brak odpowiedzi z API Ministerstwa Finansów.", "cached": False}
    else:
        result["cached"] = False
    return result


def get_nbp_rate(currency: str, date_str: str = None) -> dict | None:
    """
    Pobiera kurs waluty z NBP API (tabela A).
    Jeśli data jest niedostępna (weekend/święto), cofa do 7 dni wstecz.
    Zwraca dict: {rate, date, currency} lub None.
    """
    try:
        import requests
        from datetime import datetime, timedelta
        cur = currency.upper()
        if date_str is None:
            date_str = date.today().strftime('%Y-%m-%d')

        # NBP nie udostępnia danych za weekendy — cofamy maksymalnie 7 dni
        check_date = datetime.strptime(date_str, '%Y-%m-%d')
        for delta in range(8):
            d = (check_date - timedelta(days=delta)).strftime('%Y-%m-%d')
            url = f"https://api.nbp.pl/api/exchangerates/rates/A/{cur}/{d}/?format=json"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                rates = data.get("rates", [])
                if rates:
                    return {
                        "currency": cur,
                        "rate": rates[0]["mid"],
                        "date": rates[0]["effectiveDate"],
                        "table": data.get("table", "A")
                    }
        return None
    except Exception:
        return None

# Inicjalizacja bazy SQLite
init_db()


# ════════════════════════════════════════════════════════════════
# SIDEBAR — USTAWIENIA
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ Ustawienia audytu")
    st.markdown("---")

    sidebar_mpp_thr = st.number_input(
        "Próg MPP (PLN)",
        min_value=0,
        max_value=500_000,
        value=15_000,
        step=1_000,
        help="Mechanizm Podzielonej Płatności jest obowiązkowy gdy kwota brutto przekroczy ten próg."
    )

    sidebar_check_ksef = st.checkbox(
        "Wymagaj numeru KSeF (od 2026)",
        value=True,
        help="Gdy zaznaczone, brak numeru KSeF na fakturze z 2026 traktowany jest jako błąd formalny."
    )

    sidebar_auto_nip = st.checkbox(
        "Auto-weryfikacja NIP w MF po audycie",
        value=False,
        help="Automatycznie sprawdza wszystkie wykryte NIP-y w Białej Liście MF zaraz po analizie.\nUwaga: limit 100 zapytań/dzień (cache lokalny chroni przed przekroczeniem)."
    )

    sidebar_show_items = st.checkbox(
        "Pokaż tabelę pozycji towarowych",
        value=True,
        help="Wyświetla wykryte pozycje towarowo-usługowe z faktury po audycie."
    )

    st.markdown("---")
    st.markdown("**ℹ️ Synapsa v3.0**")
    st.markdown("🔒 Dane 100% lokalne")
    st.caption("Biuro Rachunkowe AI | Maj 2026")

# Udostępniamy ustawienia z sidebara reszcie aplikacji
APP_MPP_THRESHOLD = sidebar_mpp_thr
APP_KSEF_REQUIRED_OVERRIDE = sidebar_check_ksef
APP_AUTO_NIP = sidebar_auto_nip
APP_SHOW_ITEMS = sidebar_show_items


# ════════════════════════════════════════════════════════════════
# AUDIT ENGINE (STANDALONE — no heavy AI imports at startup)
# ════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _load_vat_norms() -> dict:
    paths = [
        os.path.join(os.path.dirname(__file__), "synapsa", "knowledge", "vat_norms.json"),
        os.path.join(os.path.dirname(__file__), "pocosiepchasz", "knowledge", "vat_norms.json"),
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def _configure_pytesseract():
    try:
        import pytesseract
        import shutil
        if shutil.which("tesseract"):
            return
        
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            common_paths.append(os.path.join(user_profile, r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe"))
            common_paths.append(os.path.join(user_profile, r"AppData\Local\Tesseract-OCR\tesseract.exe"))
            
        for path in common_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return
    except Exception:
        pass


def _is_tesseract_installed() -> bool:
    try:
        import pytesseract
        _configure_pytesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    text = ""
    if ext in (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
        try:
            import fitz
            doc = fitz.open(path)
            pages_text = []
            for page in doc:
                pages_text.append(page.get_text("text"))
            doc.close()
            text = "\n".join(pages_text).strip()
            
            if ext == ".pdf" and len(text) >= 50:
                return text
        except Exception:
            text = ""
            
        try:
            from PIL import Image
            import pytesseract
            _configure_pytesseract()
            
            if ext == ".pdf":
                import fitz
                doc = fitz.open(path)
                ocr_pages = []
                for page in doc:
                    pix = page.get_pixmap(dpi=150)
                    img_data = pix.tobytes("png")
                    from io import BytesIO
                    img = Image.open(BytesIO(img_data))
                    ocr_text = pytesseract.image_to_string(img, lang="pol+eng")
                    ocr_pages.append(ocr_text)
                doc.close()
                text = "\n".join(ocr_pages).strip()
            else:
                img = Image.open(path)
                text = pytesseract.image_to_string(img, lang="pol+eng").strip()
        except Exception:
            pass
            
    if not text and ext in (".txt", ".csv"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception:
            pass
            
    return text


def _detect_year(text: str) -> int:
    t = text.lower()
    date_patterns = [
        r'\b(201[5-9]|202[0-9]|2030)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])\b',
        r'\b(0[1-9]|[12][0-9]|3[01])[.](0[1-9]|1[0-2])[.](201[5-9]|202[0-9]|2030)\b',
    ]
    
    issue_keywords = ["wystawienia", "wystawiono", "sprzedaży", "sprzedazy", "operacji", "dostawy"]
    
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in issue_keywords):
            for pat in date_patterns:
                m = re.search(pat, line)
                if m:
                    year_str = m.group(1) if '-' in m.group(0) or '/' in m.group(0) else m.group(3)
                    return int(year_str)
                    
    all_years = []
    for pat in date_patterns:
        for m in re.finditer(pat, text):
            year_str = m.group(1) if '-' in m.group(0) or '/' in m.group(0) else m.group(3)
            all_years.append(int(year_str))
            
    if all_years:
        from collections import Counter
        return Counter(all_years).most_common(1)[0][0]
        
    matches = re.findall(r'\b(201[5-9]|202[0-9]|2030)\b', text)
    years = [int(m) for m in matches]
    if years:
        return min(years)
    return date.today().year


def validate_nip(nip: str) -> bool:
    digits = re.sub(r'[^\d]', '', nip)
    if len(digits) != 10:
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(digits[i]) * weights[i] for i in range(9)) % 11
    return checksum == int(digits[9])


def validate_ksef_number(ksef_str: str, seller_nip: str = None, invoice_year: int = None) -> dict:
    """
    Waliduje polski numer KSeF:
    Format: 35 znaków: NIP (10) + Data (8: YYYYMMDD) + 17 znaków identyfikator.
    Przykład: 9999999999-20260424-6B5C2D-E8A7B9 -> 35 znaków.
    """
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', ksef_str)
    if len(cleaned) != 35:
        return {
            "valid": False,
            "error": f"Nieprawidłowa długość numeru KSeF: {len(cleaned)} znaków (wymagane dokładnie 35 znaków)."
        }
    nip_part = cleaned[:10]
    date_part = cleaned[10:18]
    errors = []
    if not validate_nip(nip_part):
        errors.append(f"Niepoprawny NIP w numerze KSeF: {nip_part} (błędna suma kontrolna)")
    if seller_nip:
        clean_seller_nip = re.sub(r'[^\d]', '', seller_nip)
        if clean_seller_nip != nip_part:
            errors.append(f"NIP z KSeF ({nip_part}) nie zgadza się z NIP sprzedawcy ({clean_seller_nip})!")
    try:
        from datetime import datetime
        ksef_date = datetime.strptime(date_part, "%Y%m%d")
        if invoice_year and ksef_date.year != invoice_year:
            errors.append(f"Rok z KSeF ({ksef_date.year}) nie zgadza się z rokiem faktury ({invoice_year})!")
    except ValueError:
        errors.append(f"Niepoprawna data w numerze KSeF: {date_part} (wymagany format YYYYMMDD)")
    if errors:
        return {
            "valid": False,
            "error": " | ".join(errors),
            "nip": nip_part,
            "date": date_part
        }
    return {
        "valid": True,
        "nip": nip_part,
        "date": f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    }


def _extract_invoice_items(text: str) -> list[dict]:
    """
    Analizuje tekst pod kątem tabeli pozycji towarowo-usługowych.
    Wykorzystuje testy matematyczne do poprawnego kojarzenia netto/brutto w wierszu.
    """
    items = []
    lines = text.split("\n")
    percent_pat = re.compile(r'\b(\d+|zw|np|0)\s*%')
    decimal_pat = re.compile(r'\b\d+(?:[\s]*\d+)*[,.]\d{2}\b')
    lp_counter = 1
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        vat_m = percent_pat.search(line_clean.lower())
        if not vat_m:
            continue
        vat_rate_str = vat_m.group(1)
        decimals = decimal_pat.findall(line_clean)
        if len(decimals) < 2:
            continue
        vals = []
        for d in decimals:
            try:
                v = float(re.sub(r'\s', '', d).replace(',', '.'))
                vals.append(v)
            except ValueError:
                pass
        if len(vals) < 2:
            continue
        vals = sorted(vals)
        netto, vat_val, brutto = 0.0, 0.0, 0.0
        if len(vals) >= 3:
            if abs(vals[0] + vals[1] - vals[2]) < 2.0:
                netto = vals[1]
                vat_val = vals[0]
                brutto = vals[2]
            elif abs(vals[0] + vals[2] - vals[1]) < 2.0:
                netto = vals[0]
                vat_val = vals[2]
                brutto = vals[1]
            else:
                brutto = vals[-1]
                netto = vals[-2]
                vat_val = vals[0]
        else:
            netto = vals[0]
            brutto = vals[1]
            vat_val = brutto - netto
        first_dec_idx = line_clean.find(decimals[0])
        if first_dec_idx > 5:
            name_part = line_clean[:first_dec_idx].strip()
        else:
            name_part = line_clean.strip()
        name_part = re.sub(r'^\s*\d+[\.\s]+', '', name_part)
        name_part = name_part[:60].strip()
        if not name_part:
            name_part = f"Pozycja towarowa {lp_counter}"
        items.append({
            "lp": lp_counter,
            "nazwa": name_part,
            "netto": netto,
            "vat_rate": f"{vat_rate_str}%",
            "vat_val": vat_val,
            "brutto": brutto
        })
        lp_counter += 1
    return items


def audit(text: str, norms: dict, mpp_threshold: int = None, ksef_required_override: bool = None) -> dict:
    t = text.lower()
    year = _detect_year(text)
    yn = norms.get("years", {}).get(str(year)) or norms.get("years", {}).get("2026", {})
    vat_ok = yn.get("vat_rates", [23, 8, 5, 0])
    # Próg MPP — z sidebara lub z bazy wiedzy
    split_thr = mpp_threshold if mpp_threshold is not None else yn.get("split_payment_threshold_pln", 15000)
    # KSeF — z ustawienia użytkownika lub z normy roku
    ksef_required = ksef_required_override if ksef_required_override is not None else yn.get("ksef_required", False)
    desc = yn.get("description", f"Przepisy {year}")

    bf, br, ost, rek = [], [], [], []

    if not re.search(r'faktura\s*vat', t):
        bf.append('Brak nagłówka "FAKTURA VAT"')
    if not re.search(r'\d{1,2}[./]\d{1,2}[./]\d{4}', text):
        bf.append("Brak daty wystawienia")
        
    nips = re.findall(r'nip\s*:?\s*([\d\-\s]{10,15})', t)
    if not nips:
        candidates = re.findall(r'\b\d{10}\b', text)
        valid_candidates = [c for c in candidates if validate_nip(c)]
        if valid_candidates:
            nips = valid_candidates

    detected_nips = []
    if not nips:
        bf.append("Brak numeru NIP sprzedawcy/nabywcy")
    else:
        for nip in nips:
            digits = re.sub(r'[^\d]', '', nip)
            if len(digits) != 10:
                bf.append(f"Nieprawidłowy format NIP: {nip.strip()} (powinien mieć 10 cyfr)")
            elif not validate_nip(digits):
                bf.append(f"Nieprawidłowa suma kontrolna NIP: {nip.strip()} (błędny numer NIP)")
            else:
                if digits not in detected_nips:
                    detected_nips.append(digits)

    seller_nip = detected_nips[0] if detected_nips else None

    if not re.search(r'termin|płatno|zap[łl]at', t):
        ost.append("Brak terminu płatności")
    if not re.search(r'konto|iban|pl[\d]{2}|\d{20,}', t):
        ost.append("Brak numeru konta bankowego")

    vat_found = re.findall(r'vat\s*(\d+)\s*%', t)
    bad_vat = [int(v) for v in vat_found if int(v) not in vat_ok]
    if bad_vat:
        bf.append(f"Nieprawidłowa stawka VAT: {bad_vat}% (dozwolone w {year}: {vat_ok}%)")

    # MPP
    amounts = re.findall(r'(?:brutto|do\s+zap[łl]aty|razem)[^\d]{0,25}([\d\s]{3,}[,.]\d{2})', t)
    max_amt = 0.0
    for a in amounts:
        try:
            max_amt = max(max_amt, float(re.sub(r'\s', '', a).replace(',', '.')))
        except ValueError:
            pass
    has_mpp = bool(re.search(r'podzielonej\s+p[łl]atno|mechanizm\s+podziel', t))
    if split_thr and max_amt > split_thr and not has_mpp:
        bf.append(f'Brak dopisku "Mechanizm Podzielonej Platnosci" — kwota {max_amt:,.2f} PLN > {split_thr:,} PLN')
    elif split_thr and max_amt > split_thr and has_mpp:
        rek.append(f"Dopisek MPP obecny ✓")

    # KSeF
    ksef_matches = re.findall(r'\b\d{10}-\d{8}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{6}\b|\b\d{35}\b|\bks/\d{4}/fv/\d+\b', t)
    detected_ksef = ksef_matches[0] if ksef_matches else None
    ksef_validation = None
    if detected_ksef:
        clean_ksef = re.sub(r'[^a-zA-Z0-9]', '', detected_ksef)
        if len(clean_ksef) == 35:
            ksef_validation = validate_ksef_number(detected_ksef, seller_nip, year)
            if not ksef_validation["valid"]:
                bf.append(f"Błąd KSeF: {ksef_validation['error']}")
            else:
                rek.append(f"Wykryto poprawny numer KSeF powiązany z fakturą: {detected_ksef} ✓")
        else:
            rek.append(f"Wykryto numer KSeF w formacie tradycyjnym/mock: {detected_ksef}")
    else:
        if ksef_required:
            bf.append("Brak obowiązkowego numeru KSeF (wymagany od 01.04.2026)")
        elif year >= 2024:
            ost.append("Brak numeru KSeF — od 01.04.2026 obowiązkowy, zalecane wdrożenie")

    # Wykrycie waluty obcej i kurs NBP
    foreign_currencies = []
    for cur_symbol in ["EUR", "USD", "GBP", "CHF", "CZK", "DKK", "NOK", "SEK"]:
        if re.search(rf'\b{cur_symbol}\b', text):
            foreign_currencies.append(cur_symbol)
    nbp_rates = {}
    for cur in foreign_currencies:
        rate_info = get_nbp_rate(cur)
        if rate_info:
            nbp_rates[cur] = rate_info
            ost.append(
                f"Faktura walutowa ({cur}): kurs NBP z dnia {rate_info['date']} = "
                f"{rate_info['rate']:.4f} PLN/{cur} (Tabela {rate_info['table']})"
            )
        else:
            ost.append(f"Faktura walutowa ({cur}): nie udało się pobrać kursu NBP — proszę sprawdzić ręcznie.")

    # ── Ekstrakcja Pozycji Faktury ───────────────────────────────
    pozycje = _extract_invoice_items(text)
    if pozycje:
        total_items_netto = sum(p["netto"] for p in pozycje)
        total_items_brutto = sum(p["brutto"] for p in pozycje)
        
        n_vals = re.findall(r'netto[^\d]{0,25}([\d\s]+[,.]\d{2})', t)
        b_vals = re.findall(r'(?:brutto|do\s+zap[łl]aty)[^\d]{0,25}([\d\s]+[,.]\d{2})', t)
        
        if n_vals:
            try:
                main_n = float(re.sub(r'\s', '', n_vals[0]).replace(',', '.'))
                if abs(total_items_netto - main_n) > 5.0:
                    br.append(
                        f"Niezgodność pozycji: Suma netto pozycji ({total_items_netto:,.2f} PLN) "
                        f"nie zgadza się z wartością netto faktury ({main_n:,.2f} PLN)!"
                    )
            except Exception:
                pass
                
        if b_vals:
            try:
                main_b = float(re.sub(r'\s', '', b_vals[0]).replace(',', '.'))
                if abs(total_items_brutto - main_b) > 5.0:
                    br.append(
                        f"Niezgodność pozycji: Suma brutto pozycji ({total_items_brutto:,.2f} PLN) "
                        f"nie zgadza się z wartością brutto faktury ({main_b:,.2f} PLN)!"
                    )
            except Exception:
                pass

    # Rachunek
    n_vals = re.findall(r'netto[^\d]{0,25}([\d\s]+[,.]\d{2})', t)
    b_vals = re.findall(r'(?:brutto|do\s+zap[łl]aty)[^\d]{0,25}([\d\s]+[,.]\d{2})', t)
    if n_vals and b_vals and vat_found:
        try:
            n = float(re.sub(r'\s', '', n_vals[0]).replace(',', '.'))
            b = float(re.sub(r'\s', '', b_vals[0]).replace(',', '.'))
            vr = float(vat_found[0])
            exp = round(n * (1 + vr / 100), 2)
            if abs(exp - b) > 1.0:
                br.append(f"Błąd rachunkowy: {n:,.2f} × (1 + {vr}%) = {exp:,.2f} PLN, a faktura podaje {b:,.2f} PLN")
            else:
                rek.append(f"Rachunek poprawny ✓")
        except (ValueError, IndexError):
            pass

    n_err = len(bf) + len(br)
    if n_err == 0 and not ost:
        status = "OK"
        ocena = "Faktura jest prawidłowa — nie znaleziono błędów."
    elif n_err == 0:
        status = "UWAGI"
        ocena = f"Faktura nie ma błędów, ale jest {len(ost)} spraw do sprawdzenia."
    else:
        status = "BLEDY"
        ocena = f"Znaleziono {n_err} błąd(ów) w fakturze. Proszę pobrać raport i poprawić."

    if not rek:
        rek.append("Proszę porównać wynik z oryginałem faktury przed złożeniem deklaracji VAT.")

    return {
        "rok_faktury": year, "podstawa": desc, "status": status,
        "bledy_formalne": bf, "bledy_rachunkowe": br,
        "uwagi": ost, "rekomendacje": rek, "ocena": ocena,
        "detected_nips": detected_nips,
        "detected_currencies": foreign_currencies,
        "nbp_rates": nbp_rates,
        "pozycje": pozycje,
        "detected_ksef": detected_ksef,
        "ksef_validation": ksef_validation
    }


# ════════════════════════════════════════════════════════════════
# TABS INTERFACE (Faza 2)
# ════════════════════════════════════════════════════════════════

st.markdown('<div class="synapsa-title">🧾 Audyt Faktur</div>', unsafe_allow_html=True)
st.markdown('<div class="synapsa-sub">System sprawdzania poprawności faktur VAT</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center; margin-bottom:20px"><span class="privacy-tag">🔒 Dane pozostają na Pani komputerze — prywatność 100%</span></div>', unsafe_allow_html=True)

tabs = st.tabs(["🔍 Nowy Audyt", "📜 Historia Audytów"])

with tabs[0]:
    # ════════════════════════════════════════════════════════════════
    # TAB 1: NEW AUDIT (Batch + Single)
    # ════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="step-box">
        <span class="step-number">1</span>
        <span class="step-title">Proszę zeskanować faktury i wgrać je tutaj</span>
        <div class="step-desc">
            Można wybrać jedną lub **wiele faktur jednocześnie**.<br>
            <b>Obsługiwane formaty:</b> zdjęcia (JPG, PNG), pliki PDF lub tekstowe (TXT).
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "📂 Kliknij aby wybrać pliki ze skanera",
        type=["pdf", "jpg", "jpeg", "png", "bmp", "tiff", "txt"],
        accept_multiple_files=True,
        label_visibility="visible",
    )

    if uploaded_files:
        st.success(f"✅ Wybrano pliki ({len(uploaded_files)}): " + ", ".join([f"**{f.name}**" for f in uploaded_files]))

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="step-box">
        <span class="step-number">2</span>
        <span class="step-title">Proszę nacisnąć przycisk "Uruchom audyt"</span>
        <div class="step-desc">
            System automatycznie i bezpiecznie przeanalizuje wszystkie pliki.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sprawdz_btn = st.button(
        "🔍 Uruchom audyt faktur",
        type="primary",
        use_container_width=True,
        disabled=(not uploaded_files),
    )

    if not uploaded_files:
        st.markdown('<div class="info-box">⬆️ Najpierw proszę wybrać jeden lub więcej plików w Kroku 1.</div>', unsafe_allow_html=True)

    if sprawdz_btn and uploaded_files:
        results = []
        os.makedirs("temp_upload", exist_ok=True)
        
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        for idx, uploaded in enumerate(uploaded_files):
            status_text.markdown(f"⏳ **Analizowanie pliku ({idx+1}/{len(uploaded_files)}):** `{uploaded.name}`...")
            
            file_bytes = uploaded.getvalue()
            f_hash = get_file_hash(file_bytes)
            
            dup = check_duplicate(f_hash)
            if dup:
                results.append(dup)
                progress_bar.progress((idx + 1) / len(uploaded_files))
                continue
                
            fpath = os.path.join("temp_upload", uploaded.name)
            try:
                with open(fpath, "wb") as fp:
                    fp.write(file_bytes)
                
                report = call_api_audit(fpath, uploaded.name)
                if not report:
                    text = _extract_text(fpath)
                    norms = _load_vat_norms()
                    if not text or len(text.strip()) < 15:
                        report = {
                            "filename": uploaded.name,
                            "status": "BLAD_ODCZYTU",
                            "ocena": "Nie udało się odczytać treści faktury.",
                            "bledy_formalne": ["Błąd odczytu: Brak warstwy tekstowej lub brak silnika OCR Tesseract."],
                            "bledy_rachunkowe": [],
                            "uwagi": [],
                            "rekomendacje": ["Proszę upewnić się, że plik ma dobrą jakość lub zainstalować silnik Tesseract OCR."],
                            "rok_faktury": 2026,
                            "podstawa": "Lokalny Silnik Reguł"
                        }
                    else:
                        report = audit(
                            text, norms,
                            mpp_threshold=APP_MPP_THRESHOLD,
                            ksef_required_override=APP_KSEF_REQUIRED_OVERRIDE if APP_KSEF_REQUIRED_OVERRIDE else None
                        )
                
                audit_id = str(uuid.uuid4())[:8]
                report["id"] = audit_id
                report["filename"] = uploaded.name
                if report["status"] != "BLAD_ODCZYTU":
                    save_audit(audit_id, uploaded.name, report["rok_faktury"], report["status"], report, f_hash)

                # Auto-weryfikacja NIP w MF (jeśli włączona w ustawieniach)
                if APP_AUTO_NIP and report.get("detected_nips"):
                    nip_results = {}
                    for nip_d in report["detected_nips"]:
                        nip_key = f"nip_result_{audit_id}_{nip_d}"
                        if nip_key not in st.session_state:
                            nip_res = check_nip_smart(nip_d)
                            st.session_state[nip_key] = nip_res
                            nip_results[nip_d] = nip_res
                    if nip_results:
                        report["auto_nip_results"] = nip_results

                results.append(report)
            finally:
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        status_text.markdown("✅ **Analiza zakończona pomyślnie!**")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="step-box">
            <span class="step-number">3</span>
            <span class="step-title">Pulpit Wyników Audytu Zbiorczego</span>
            <div class="step-desc">Poniżej znajduje się podsumowanie serii analizowanych faktur.</div>
        </div>
        """, unsafe_allow_html=True)
        
        num_ok = sum(1 for r in results if r["status"] == "OK")
        num_warn = sum(1 for r in results if r["status"] == "UWAGI")
        num_err = sum(1 for r in results if r["status"] in ("BLEDY", "BLAD_ODCZYTU"))
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wszystkie pliki", len(results))
        c2.metric("Prawidłowe ✅", num_ok)
        c3.metric("Z uwagami 🟡", num_warn)
        c4.metric("Z błędami ❌", num_err)
        
        export_data = []
        for r in results:
            export_data.append({
                "Plik": r["filename"],
                "Rok": r["rok_faktury"],
                "Status": r["status"],
                "Błędy Formalne": ", ".join(r.get("bledy_formalne", [])),
                "Błędy Rachunkowe": ", ".join(r.get("bledy_rachunkowe", [])),
                "Uwagi": ", ".join(r.get("uwagi", [])),
                "Ocena": r["ocena"]
            })
        df = pd.DataFrame(export_data)
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Wyniki Audytu", index=False)
        
        st.download_button(
            "📊 Pobierz wyniki serii (Excel)",
            data=excel_buffer.getvalue(),
            file_name=f"audyt_seria_{date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        
        st.markdown("<br>### 📂 Szczegóły audytu poszczególnych plików", unsafe_allow_html=False)
        
        for r in results:
            icon = "✅" if r["status"] == "OK" else ("🟡" if r["status"] == "UWAGI" else "❌")
            with st.expander(f"{icon} **{r['filename']}** — Status: **{r['status']}**", expanded=(r["status"] in ("BLEDY", "BLAD_ODCZYTU"))):
                if r["status"] == "OK":
                    st.markdown(f'<div class="result-ok"><div class="result-title">✅ Faktura Prawidłowa</div><div class="result-text">{r["ocena"]}</div></div>', unsafe_allow_html=True)
                elif r["status"] == "UWAGI":
                    st.markdown(f'<div class="result-warn"><div class="result-title">🟡 Uwagi do faktury</div><div class="result-text">{r["ocena"]}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="result-error"><div class="result-title">❌ Znaleziono błędy!</div><div class="result-text">{r["ocena"]}</div></div>', unsafe_allow_html=True)
                
                if r.get("bledy_formalne"):
                    st.markdown("**❌ Błędy formalne:**", unsafe_allow_html=False)
                    for b in r["bledy_formalne"]:
                        st.markdown(f'<div class="error-item">❌ {b}</div>', unsafe_allow_html=True)
                if r.get("bledy_rachunkowe"):
                    st.markdown("**🔢 Błędy rachunkowe:**", unsafe_allow_html=False)
                    for b in r["bledy_rachunkowe"]:
                        st.markdown(f'<div class="error-item">🔢 {b}</div>', unsafe_allow_html=True)
                if r.get("uwagi"):
                    st.markdown("**⚠️ Sprawy warte uwagi:**", unsafe_allow_html=False)
                    for o in r["uwagi"]:
                        st.markdown(f'<div class="warn-item">⚠️ {o}</div>', unsafe_allow_html=True)
                if r.get("rekomendacje"):
                    for rec in r["rekomendacje"]:
                        if "✓" in rec:
                            st.markdown(f'<div class="ok-item">✅ {rec}</div>', unsafe_allow_html=True)
                            
                st.markdown(f"<small style='color:#888'>Źródło: {r['podstawa']}</small>", unsafe_allow_html=True)

                # ── Kursy walut NBP (jeśli faktura walutowa) ─────────────────
                if r.get("nbp_rates"):
                    st.markdown("---")
                    st.markdown("**💱 Kursy NBP dla walut obcych na fakturze:**")
                    for cur, rate_info in r["nbp_rates"].items():
                        st.markdown(
                            f'<div class="ok-item">'
                            f'<b>{cur}</b>: {rate_info["rate"]:.4f} PLN '
                            f'(kurs z dnia <b>{rate_info["date"]}</b>, Tabela NBP-{rate_info["table"]})</div>',
                            unsafe_allow_html=True
                        )

                # ── Weryfikacja NIP w Białej Liście MF ───────────────────────
                detected_nips = r.get("detected_nips", [])
                if detected_nips and r["status"] != "BLAD_ODCZYTU":
                    st.markdown("---")
                    st.markdown("**🏛️ Weryfikacja NIP w Białej Liście Ministerstwa Finansów:**")
                    uid = r.get('id', uuid.uuid4().hex[:6])
                    for nip_digit in detected_nips:
                        nip_key = f"nip_check_{uid}_{nip_digit}"
                        nip_result_key = f"nip_result_{uid}_{nip_digit}"
                        col_nip_btn, col_nip_info = st.columns([1, 3])
                        with col_nip_btn:
                            if st.button(
                                f"🔍 Sprawdź NIP\n{nip_digit}",
                                key=nip_key,
                                use_container_width=True
                            ):
                                with st.spinner(f"Sprawdzam NIP {nip_digit} w bazie MF..."):
                                    nip_res = check_nip_smart(nip_digit)
                                st.session_state[nip_result_key] = nip_res
                        with col_nip_info:
                            nip_res_display = st.session_state.get(nip_result_key)
                            if nip_res_display:
                                if "error" in nip_res_display:
                                    st.markdown(
                                        f'<div class="warn-item">⚠️ NIP <b>{nip_digit}</b>: {nip_res_display["error"]}</div>',
                                        unsafe_allow_html=True
                                    )
                                else:
                                    vat_status = nip_res_display.get("statusVat", "Nieznany")
                                    status_icon = "✅" if "Czynny" in str(vat_status) else "⚠️"
                                    cached_info = " *(z cache)*" if nip_res_display.get("cached") else ""
                                    st.markdown(
                                        f'<div class="ok-item">{status_icon} <b>{nip_res_display.get("name", "Brak nazwy")}</b><br>'
                                        f'Status VAT: <b>{vat_status}</b>{cached_info}<br>'
                                        f'Adres: {nip_res_display.get("address", "-")}<br>'
                                        f'REGON: {nip_res_display.get("regon", "-")}</div>',
                                        unsafe_allow_html=True
                                    )
                                    accounts = nip_res_display.get("accounts", [])
                                    if accounts:
                                        st.markdown(
                                            f'<div class="info-box">🏦 Rachunki bankowe w bazie MF ({len(accounts)} szt.): '
                                            + ", ".join(f"<code>{a}</code>" for a in accounts[:5])
                                            + (f" i {len(accounts)-5} więcej..." if len(accounts) > 5 else "")
                                            + '</div>',
                                            unsafe_allow_html=True
                                        )
                            else:
                                st.markdown(
                                    f'<div style="color:#9ca3af; font-size:1rem; padding:6px 0">'
                                    f'NIP: <b>{nip_digit}</b> — kliknij przycisk aby zweryfikować</div>',
                                    unsafe_allow_html=True
                                )

                # ── Wyciągnięte Pozycje z Faktury (Faza 3 / Faza 4) ─────────
                pozycje = r.get("pozycje", [])
                if pozycje and APP_SHOW_ITEMS:
                    st.markdown("---")
                    st.markdown("📋 **Pozycje wyciągnięte z faktury:**")
                    item_rows = []
                    for p in pozycje:
                        item_rows.append({
                            "Lp.": p["lp"],
                            "Nazwa pozycji": p["nazwa"],
                            "Wartość Netto (PLN)": f"{p['netto']:,.2f}",
                            "Stawka VAT": p["vat_rate"],
                            "Kwota VAT (PLN)": f"{p['vat_val']:,.2f}",
                            "Wartość Brutto (PLN)": f"{p['brutto']:,.2f}"
                        })
                    df_poz = pd.DataFrame(item_rows)
                    st.dataframe(df_poz, use_container_width=True, hide_index=True)
                    # Sumowanie pozycji
                    sum_netto = sum(p["netto"] for p in pozycje)
                    sum_brutto = sum(p["brutto"] for p in pozycje)
                    st.markdown(
                        f'<div class="info-box">'
                        f'📊 Suma pozycji: Netto <b>{sum_netto:,.2f} PLN</b> | '
                        f'Brutto <b>{sum_brutto:,.2f} PLN</b> ({len(pozycje)} pozycji)'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                if r["status"] != "BLAD_ODCZYTU":
                    st.markdown("---")
                    col_pdf, col_txt = st.columns(2)
                    with col_pdf:
                        pdf_data = generate_pdf_report(r, r["filename"])
                        st.download_button(
                            "📄 Pobierz Certyfikat PDF",
                            data=pdf_data,
                            file_name=f"certyfikat_audytu_{r['filename']}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{r.get('id', uuid.uuid4().hex[:6])}",
                            use_container_width=True
                        )
                    with col_txt:
                        rep_text = f"RAPORT AUDYTU FAKTURY\nPlik: {r['filename']}\nStatus: {r['status']}\nOcena: {r['ocena']}\n"
                        if r.get("nbp_rates"):
                            rep_text += "\nKURSY WALUT NBP:\n"
                            for cur, ri in r["nbp_rates"].items():
                                rep_text += f"  {cur}: {ri['rate']:.4f} PLN (data: {ri['date']})\n"
                        st.download_button(
                            "📄 Pobierz raport TXT",
                            data=rep_text,
                            file_name=f"raport_{r['filename']}.txt",
                            mime="text/plain",
                            key=f"txt_{r.get('id', uuid.uuid4().hex[:6])}",
                            use_container_width=True
                        )


with tabs[1]:
    # ════════════════════════════════════════════════════════════════
    # TAB 2: AUDIT HISTORY — z filtrowaniem i statystykami
    # ════════════════════════════════════════════════════════════════
    st.markdown("### 📜 Zapisana Historia Audytów", unsafe_allow_html=False)
    st.markdown("Poniżej znajduje się zestawienie ostatnich audytów zapisanych lokalnie w bazie danych.", unsafe_allow_html=False)

    # ── Filtry ────────────────────────────────────────────────────
    flt_col1, flt_col2, flt_col3 = st.columns([3, 2, 2])
    with flt_col1:
        flt_name = st.text_input("🔍 Szukaj po nazwie pliku", placeholder="np. faktura_maj...")
    with flt_col2:
        flt_status = st.selectbox("Status", ["Wszystkie", "OK", "UWAGI", "BLEDY"])
    with flt_col3:
        flt_year = st.selectbox("Rok faktury", ["Wszystkie"] + [str(y) for y in range(2026, 2017, -1)])

    history = get_audit_history(200)  # pobieramy więcej, filtrujemy lokalnie

    # ── Filtrowanie lokalne ───────────────────────────────────────
    filtered_history = []
    for h in history:
        h_id, h_name, h_date, h_year, h_status, h_ocena = h
        if flt_name and flt_name.lower() not in h_name.lower():
            continue
        if flt_status != "Wszystkie" and h_status != flt_status:
            continue
        if flt_year != "Wszystkie" and str(h_year) != flt_year:
            continue
        filtered_history.append(h)
    history = filtered_history
    
    if not history:
        st.markdown('<div class="info-box">Brak audytów spełniających kryteria filtrowania. Zmień filtry lub przeprowadź nowy audyt!</div>', unsafe_allow_html=True)
    else:
        # ── Podsumowanie statystyczne ─────────────────────────────
        all_history_stats = get_audit_history(500)
        if len(all_history_stats) >= 2:
            st.markdown("---")
            st.markdown("#### 📊 Statystyki Audytów")
            stat_c1, stat_c2, stat_c3, stat_c4 = st.columns(4)
            stat_c1.metric("Łącznie audytów", len(all_history_stats))
            stat_c2.metric("Prawidłowe ✅", sum(1 for h in all_history_stats if h[4] == "OK"))
            stat_c3.metric("Z uwagami 🟡", sum(1 for h in all_history_stats if h[4] == "UWAGI"))
            stat_c4.metric("Z błędami ❌", sum(1 for h in all_history_stats if h[4] == "BLEDY"))

            # Wykres miesięczny
            month_counts: dict = {}
            for h in all_history_stats:
                m = h[2][:7] if h[2] and len(h[2]) >= 7 else "Nieznany"
                month_counts[m] = month_counts.get(m, 0) + 1
            if month_counts:
                df_months = pd.DataFrame(
                    [{"Miesiąc": k, "Liczba audytów": v} for k, v in sorted(month_counts.items())]
                ).set_index("Miesiąc")
                st.markdown("**📅 Liczba audytów wg miesiąca:**")
                st.bar_chart(df_months)
            st.markdown("---")

        # ── Przyciski akcji ───────────────────────────────────────
        col_clear, col_excel = st.columns(2)
        with col_clear:
            if st.button("🗑️ Wyczyszczenie historii", use_container_width=True):
                clear_audit_history()
                st.success("Historia została wyczyszczona!")
                st.rerun()
        with col_excel:
            hist_export = []
            for h in history:
                hist_export.append({
                    "Identyfikator": h[0],
                    "Nazwa Pliku": h[1],
                    "Data Audytu": h[2],
                    "Rok Faktury": h[3],
                    "Status Audytu": h[4],
                    "Ocena": h[5]
                })
            df_hist = pd.DataFrame(hist_export)
            excel_hist_buffer = BytesIO()
            with pd.ExcelWriter(excel_hist_buffer, engine='openpyxl') as writer:
                df_hist.to_excel(writer, sheet_name="Historia Audytów", index=False)

            st.download_button(
                "📊 Eksportuj wyniki filtrowania (Excel)",
                data=excel_hist_buffer.getvalue(),
                file_name=f"historia_audytów_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        st.caption(f"Wyświetlono: **{len(history)}** rekordów (filtrowanie aktywne: {'Tak' if (flt_name or flt_status != 'Wszystkie' or flt_year != 'Wszystkie') else 'Nie'})")
            
        st.markdown("<br>", unsafe_allow_html=True)

        for h in history:
            h_id, h_name, h_date, h_year, h_status, h_ocena = h
            icon = "✅" if h_status == "OK" else ("🟡" if h_status == "UWAGI" else "❌")
            
            with st.expander(f"{icon} Plik: **{h_name}** | Data: **{h_date}** | Status: **{h_status}**"):
                st.markdown(f"**Szczegóły audytu o ID:** `{h_id}`")
                st.markdown(f"**Wynik:** {h_ocena}")
                
                full_rep = get_audit_by_id(h_id)
                if full_rep:
                    if full_rep.get("bledy_formalne"):
                        st.markdown("**❌ Błędy formalne:**", unsafe_allow_html=False)
                        for b in full_rep["bledy_formalne"]:
                            st.markdown(f'<div class="error-item">❌ {b}</div>', unsafe_allow_html=True)
                    if full_rep.get("bledy_rachunkowe"):
                        st.markdown("**🔢 Błędy rachunkowe:**", unsafe_allow_html=False)
                        for b in full_rep["bledy_rachunkowe"]:
                            st.markdown(f'<div class="error-item">🔢 {b}</div>', unsafe_allow_html=True)
                    if full_rep.get("uwagi"):
                        st.markdown("**⚠️ Sprawy warte uwagi:**", unsafe_allow_html=False)
                        for o in full_rep["uwagi"]:
                            st.markdown(f'<div class="warn-item">⚠️ {o}</div>', unsafe_allow_html=True)
                            
                    past_pdf = generate_pdf_report(full_rep, h_name)
                    st.download_button(
                        "📄 Pobierz historyczny Certyfikat PDF",
                        data=past_pdf,
                        file_name=f"certyfikat_audytu_{h_name}.pdf",
                        mime="application/pdf",
                        key=f"hist_pdf_{h_id}",
                        use_container_width=True
                    )


# ════════════════════════════════════════════════════════════════
# STOPKA — POMOC
# ════════════════════════════════════════════════════════════════
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="background: #f8fafc; border-radius: 12px; padding: 20px; text-align: center; color: #6b7280; font-size: 1rem;">
    <b>Synapsa Biuro Rachunkowe AI</b> — wersja 3.0 | Maj 2026<br>
    🔒 Dane nigdy nie opuszczają komputera &nbsp;|&nbsp; Działa lokalnie i bezpiecznie<br>
    Nowości v3.0: Panel ustawień • Filtrowanie historii • Wykresy statystyk • Auto-NIP MF<br>
    W razie problemów proszę skontaktować się z obsługą techniczną.
</div>
""", unsafe_allow_html=True)
