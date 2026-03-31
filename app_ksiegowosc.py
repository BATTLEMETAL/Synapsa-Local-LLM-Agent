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
from datetime import date

st.set_page_config(
    page_title="Synapsa — Audyt Faktur",
    page_icon="🧾",
    layout="centered",
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


def _extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
        try:
            import fitz
            doc = fitz.open(path)
            text = "\n".join(page.get_text("text") for page in doc)
            doc.close()
            if text.strip():
                return text.strip()
            # scanned image fallback — return raw text from words
            doc2 = fitz.open(path)
            words = []
            for page in doc2:
                words += [w[4] for w in page.get_text("words")]
            doc2.close()
            return " ".join(words)
        except ImportError:
            return ""
        except Exception:
            return ""
    if ext in (".txt", ".csv"):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


def _detect_year(text: str) -> int:
    matches = re.findall(r'\b(201[5-9]|202[0-9])\b', text)
    years = [int(m) for m in matches if 2015 <= int(m) <= 2030]
    return max(years) if years else 2026


def audit(text: str, norms: dict) -> dict:
    t = text.lower()
    year = _detect_year(text)
    yn = norms.get("years", {}).get(str(year)) or norms.get("years", {}).get("2026", {})
    vat_ok = yn.get("vat_rates", [23, 8, 5, 0])
    ksef_required = yn.get("ksef_required", False)
    split_thr = yn.get("split_payment_threshold_pln", 15000)
    desc = yn.get("description", f"Przepisy {year}")

    bf, br, ost, rek = [], [], [], []

    if not re.search(r'faktura\s*vat', t):
        bf.append('Brak nagłówka "FAKTURA VAT"')
    if not re.search(r'\d{1,2}[./]\d{1,2}[./]\d{4}', text):
        bf.append("Brak daty wystawienia")
    nips = re.findall(r'nip\s*:?\s*([\d\-\s]{10,14})', t)
    if not nips:
        bf.append("Brak numeru NIP")
    else:
        for nip in nips:
            digits = re.sub(r'[^\d]', '', nip)
            if digits and len(digits) != 10:
                bf.append(f"Nieprawidłowy NIP: {nip.strip()} — powinien mieć 10 cyfr")
                break

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
    has_ksef = bool(re.search(r'ksef|ksej', t))
    if ksef_required and not has_ksef:
        bf.append("Brak numeru KSeF — obowiązkowy od 01.04.2026")
    elif year >= 2024 and not has_ksef:
        ost.append("Brak numeru KSeF — od 01.04.2026 obowiązkowy, warto go dołączyć")

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
    }


# ════════════════════════════════════════════════════════════════
# PAGE HEADER
# ════════════════════════════════════════════════════════════════
st.markdown('<div class="synapsa-title">🧾 Audyt Faktur</div>', unsafe_allow_html=True)
st.markdown('<div class="synapsa-sub">System sprawdzania poprawności faktur VAT</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center; margin-bottom:30px"><span class="privacy-tag">🔒 Dane pozostają na Pani komputerze — prywatność 100%</span></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# KROK 1
# ════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-box">
    <span class="step-number">1</span>
    <span class="step-title">Proszę zeskanować fakturę i wgrać skan tutaj</span>
    <div class="step-desc">
        Drukarka/skaner zapisuje plik na komputerze (np. na Pulpicie lub w folderze Dokumenty).<br>
        Proszę kliknąć przycisk poniżej i wskazać ten plik.
        <br><br>
        <b>Obsługiwane formaty:</b> zdjęcie ze skanera (JPG, PNG), plik PDF, lub plik tekstowy (TXT).
    </div>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "📂 Kliknij aby wybrać plik ze skanera",
    type=["pdf", "jpg", "jpeg", "png", "bmp", "tiff", "txt"],
    accept_multiple_files=False,
    label_visibility="visible",
)

if uploaded:
    st.success(f"✅ Plik wybrany: **{uploaded.name}**")

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# KROK 2
# ════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-box">
    <span class="step-number">2</span>
    <span class="step-title">Proszę nacisnąć przycisk "Sprawdź fakturę"</span>
    <div class="step-desc">
        System automatycznie przeanalizuje fakturę i wyświetli wyniki.
    </div>
</div>
""", unsafe_allow_html=True)

sprawdz_btn = st.button(
    "🔍 Sprawdź fakturę",
    type="primary",
    use_container_width=True,
    disabled=(uploaded is None),
)

if uploaded is None:
    st.markdown('<div class="info-box">⬆️ Najpierw proszę wybrać plik w Kroku 1, a następnie nacisnąć przycisk powyżej.</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# KROK 3: WYNIKI
# ════════════════════════════════════════════════════════════════
if sprawdz_btn and uploaded:

    os.makedirs("temp_upload", exist_ok=True)
    fpath = os.path.join("temp_upload", uploaded.name)
    with open(fpath, "wb") as fp:
        fp.write(uploaded.getbuffer())

    with st.spinner("⏳ Trwa analiza faktury... Proszę chwilę poczekać."):
        text = _extract_text(fpath)
        norms = _load_vat_norms()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
<div class="step-box">
    <span class="step-number">3</span>
    <span class="step-title">Wyniki sprawdzenia faktury</span>
    <div class="step-desc">Poniżej widać czy faktura jest prawidłowa.</div>
</div>
""", unsafe_allow_html=True)

    if not text or len(text.strip()) < 15:
        st.markdown("""
<div class="result-error">
    <div class="result-title">⚠️ Nie udało się odczytać faktury</div>
    <div class="result-text">
        System nie mógł odczytać treści z pliku. Proszę spróbować:<br>
        • Zapisać skan jako PDF (najlepsza jakość)<br>
        • Upewnić się, że skan ma dobrą jakość (nie jest za ciemny ani rozmazany)<br>
        • Poprosić o pomoc
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        report = audit(text, norms)
        status = report["status"]
        rok = report["rok_faktury"]

        # GŁÓWNY WYNIK — BARDZO DUŻY
        if status == "OK":
            st.markdown(f"""
<div class="result-ok">
    <div class="result-title">✅ Faktura jest PRAWIDŁOWA</div>
    <div class="result-text">
        Rok faktury: <b>{rok}</b><br>
        {report["ocena"]}
    </div>
</div>
""", unsafe_allow_html=True)

        elif status == "UWAGI":
            st.markdown(f"""
<div class="result-warn">
    <div class="result-title">🟡 Faktura nie ma błędów, ale są uwagi</div>
    <div class="result-text">
        Rok faktury: <b>{rok}</b><br>
        {report["ocena"]}
    </div>
</div>
""", unsafe_allow_html=True)

        else:  # BLEDY
            st.markdown(f"""
<div class="result-error">
    <div class="result-title">❌ W fakturze znaleziono błędy!</div>
    <div class="result-text">
        Rok faktury: <b>{rok}</b><br>
        {report["ocena"]}
    </div>
</div>
""", unsafe_allow_html=True)

        # Błędy formalne
        if report["bledy_formalne"]:
            st.markdown("<br>**❌ Błędy formalne do poprawy:**", unsafe_allow_html=False)
            for b in report["bledy_formalne"]:
                st.markdown(f'<div class="error-item">❌ {b}</div>', unsafe_allow_html=True)

        # Błędy rachunkowe
        if report["bledy_rachunkowe"]:
            st.markdown("<br>**🔢 Błędy rachunkowe (złe liczby):**", unsafe_allow_html=False)
            for b in report["bledy_rachunkowe"]:
                st.markdown(f'<div class="error-item">🔢 {b}</div>', unsafe_allow_html=True)

        # Uwagi
        if report["uwagi"]:
            st.markdown("<br>**⚠️ Sprawy warte uwagi:**", unsafe_allow_html=False)
            for o in report["uwagi"]:
                st.markdown(f'<div class="warn-item">⚠️ {o}</div>', unsafe_allow_html=True)

        # Rekomendacje
        if report["rekomendacje"]:
            for r in report["rekomendacje"]:
                if "✓" in r:
                    st.markdown(f'<div class="ok-item">✅ {r}</div>', unsafe_allow_html=True)

        # Podstawa prawna (małym tekstem, nieważne dla starszej osoby)
        st.markdown(f"<br><small style='color:#888'>Podstawa: {report['podstawa']} | Analiza offline — dane nie opuściły komputera</small>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # KROK 4: POBIERZ RAPORT
        st.markdown("""
<div class="step-box">
    <span class="step-number">4</span>
    <span class="step-title">Proszę pobrać raport (opcjonalnie)</span>
    <div class="step-desc">
        Raport można zapisać do pliku i wydrukować jako dokumentację.
    </div>
</div>
""", unsafe_allow_html=True)

        report_text = f"""RAPORT AUDYTU FAKTURY
Data sprawdzenia: {date.today().strftime('%d.%m.%Y')}
Plik: {uploaded.name}
Rok faktury: {rok}
Wynik: {status}

{report['ocena']}

BŁĘDY FORMALNE ({len(report['bledy_formalne'])}):
""" + ("\n".join(f"  - {b}" for b in report["bledy_formalne"]) or "  Brak") + f"""

BŁĘDY RACHUNKOWE ({len(report['bledy_rachunkowe'])}):
""" + ("\n".join(f"  - {b}" for b in report["bledy_rachunkowe"]) or "  Brak") + f"""

UWAGI ({len(report['uwagi'])}):
""" + ("\n".join(f"  - {o}" for o in report["uwagi"]) or "  Brak") + f"""

{report['podstawa']}
System: Synapsa Biuro Rachunkowe AI v2.1 | Analiza lokalna"""

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📄 Pobierz raport (TXT)",
                data=report_text,
                file_name=f"audyt_{date.today().strftime('%Y%m%d')}_{uploaded.name}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "📊 Pobierz raport (JSON)",
                data=json.dumps(report, ensure_ascii=False, indent=2),
                file_name=f"audyt_{date.today().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True,
            )

        # KROK 5: NOWA FAKTURA
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Sprawdź kolejną fakturę", use_container_width=True):
            st.rerun()

# ════════════════════════════════════════════════════════════════
# STOPKA — POMOC
# ════════════════════════════════════════════════════════════════
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="background: #f8fafc; border-radius: 12px; padding: 20px; text-align: center; color: #6b7280; font-size: 1rem;">
    <b>Synapsa Biuro Rachunkowe AI</b> — wersja 2.1 MVP | Marzec 2026<br>
    🔒 Dane nigdy nie opuszczają komputera &nbsp;|&nbsp; Działa bez internetu<br>
    W razie problemów proszę skontaktować się z obsługą techniczną.
</div>
""", unsafe_allow_html=True)
