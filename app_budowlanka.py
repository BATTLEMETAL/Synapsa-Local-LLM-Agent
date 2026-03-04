"""
Synapsa Budowlanka - Professional Edition
Unified Streamlit App — przebudowana z naciskiem na stabilność.
Wszystkie komponenty mają fallbacki — aplikacja ZAWSZE się uruchomi.
"""
import streamlit as st
import os
import sys
import json

# === ŚCIEŻKA PROJEKTU ===
_root = os.path.abspath(os.path.dirname(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

# === IMPORT AGENTÓW (z obsługą błędów) ===
IMPORT_ERROR = None
try:
    # Windows compatibility FIRST
    from synapsa.compat import setup_windows_compatibility
    setup_windows_compatibility()

    from synapsa.agents.office_agent import SecureAuditAgent
    from synapsa.agents.construction_agent import ConstructionChatAgent
    from synapsa.agents.accountant_agent import AccountantAgent
    from synapsa.agents.zlecenie_processor import ZlecenieProcessor
    from synapsa.hardware import scan_hardware, determine_profile
except ImportError as e:
    IMPORT_ERROR = str(e)
except Exception as e:
    IMPORT_ERROR = str(e)

# === STRONA STREAMLIT ===
st.set_page_config(
    page_title="Synapsa Budowlanka",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# === CSS (Profesjonalny wygląd) ===
st.markdown("""
<style>
    /* Dark theme boost */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF9800, #FF5722);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 10px 0;
    }
    .status-box {
        background: #1E1E2E;
        border-left: 4px solid #FF9800;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1A2E;
        border-radius: 8px 8px 0 0;
        color: #CCC;
        font-weight: 600;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #FF9800, #FF5722);
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown('<div class="main-header">🏗️ Synapsa Budowlanka Edition</div>', unsafe_allow_html=True)

# Alert jeśli błąd importu (nie crashuje aplikacji!)
if IMPORT_ERROR:
    st.warning(f"⚠️ Tryb demo — brak pełnych bibliotek AI: `{IMPORT_ERROR}`\n\nAplikacja działa w trybie offline z predefinowanymi odpowiedziami.")

# Status bar
synapsa_config = {}
if os.path.exists("synapsa_config.json"):
    try:
        with open("synapsa_config.json") as f:
            synapsa_config = json.load(f)
    except Exception:
        pass

if synapsa_config:
    tier = synapsa_config.get("tier", "UNKNOWN")
    desc = synapsa_config.get("description", "")
    st.markdown(f'<div class="status-box">🖥️ <b>Profil AI:</b> {tier} — {desc}</div>', unsafe_allow_html=True)

# === ZAKŁADKI ===
tab_zlecenie, tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Nowe Zlecenie → Faktura",
    "💬 Asystent Budowlany",
    "🕵️ Audyt Faktur",
    "👩‍💼 Wirtualna Księgowa",
    "🖥️ System & Sprzęt"
])

# ─────────────────────────────────────────
# TAB 0: NOWE ZLECENIE → FAKTURA (GŁÓWNA)
# ─────────────────────────────────────────
with tab_zlecenie:
    st.header("📋 Nowe Zlecenie → Kosztorys → Faktura")
    st.caption(
        "Opisz zlecenie naturalnym językiem. System automatycznie obliczy koszty "
        "i wystawi fakturę — w stylu Twoich poprzednich faktur (jeśli zostały wgrane)."
    )

    # Przykłady do kliknięcia
    st.markdown("**Przykładowe zlecenia (kliknij aby wypełnić):**")
    ex_cols = st.columns(3)
    examples = [
        "mam nowe zlecenie budowanie kostki brukowej, cena 150 za metr kwadratowy, 200m2",
        "zlecenie: ocieplenie budynku styropianem 15cm, 350m2, stawka 85 zł/m2",
        "remont elewacji + tynkowanie, 180m2, cena 120 PLN za m2",
    ]
    for i, ex in enumerate(examples):
        if ex_cols[i].button(f"📌 Przykład {i+1}", key=f"ex_{i}"):
            st.session_state["zlecenie_input"] = ex

    st.divider()

    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        zlecenie_text = st.text_area(
            "📝 Opis zlecenia (w dowolnym języku naturalnym)",
            value=st.session_state.get("zlecenie_input", ""),
            height=120,
            placeholder="Np. 'mam nowe zlecenie budowanie kostki brukowej, cena 150 za metr kwadratowy, działka 200m2'",
            key="zlecenie_text_area",
        )

    with col_right:
        sprzedawca = st.text_input(
            "🏢 Twoja firma (Sprzedawca)",
            placeholder="Np. Budowlanka Sp. z o.o., NIP: 123-456-78-90",
            key="sprzedawca_input",
        )
        nabywca = st.text_input(
            "👤 Klient (Nabywca)",
            placeholder="Np. Jan Kowalski, NIP: 987-654-32-10",
            key="nabywca_input",
        )

    if st.button("⚡ Oblicz i wystaw fakturę", type="primary", key="zlecenie_go", use_container_width=True):
        if not zlecenie_text or len(zlecenie_text.strip()) < 5:
            st.error("❌ Wpisz opis zlecenia.")
        else:
            with st.spinner("🔄 Analizuję zlecenie..."):
                try:
                    processor = ZlecenieProcessor()
                    result = processor.process(
                        zlecenie_text,
                        nabywca=nabywca,
                        sprzedawca=sprzedawca,
                    )
                    st.session_state["zlecenie_result"] = result
                except NameError:
                    # ZlecenieProcessor nie załadowany — offline z dostępnym modułem
                    import sys, os
                    _r = os.path.abspath(os.path.dirname(__file__))
                    if _r not in sys.path:
                        sys.path.insert(0, _r)
                    from synapsa.agents.zlecenie_processor import ZlecenieProcessor as _ZP
                    processor = _ZP()
                    result = processor.process(zlecenie_text, nabywca=nabywca, sprzedawca=sprzedawca)
                    st.session_state["zlecenie_result"] = result
                except Exception as e:
                    st.error(f"❌ Błąd: {e}")

    # Wyświetl wyniki
    r = st.session_state.get("zlecenie_result")
    if r:
        if r.get("status") == "error":
            st.error(f"⚠️ {r['error']}")
            if r.get("parse"):
                with st.expander("Dane parsowania"):
                    st.json(r["parse"])
        else:
            st.success(f"✅ Faktura nr **{r['invoice_nr']}** wystawiona | Data: {r['invoice_date']}")

            res_col1, res_col2 = st.columns(2, gap="large")

            # KOSZTORYS
            with res_col1:
                st.subheader("📊 Kosztorys")
                calc = r["calc"]
                parse = r["parse"]

                st.markdown(f"**Rodzaj pracy:** {parse['typ_pracy'].title()}")
                if calc["metraz"] > 0:
                    st.markdown(f"**Metraż:** {calc['metraz']:,.0f} {calc['jednostka']}")
                    st.markdown(f"**Cena/m²:** {calc['cena_m2']:,.2f} PLN")

                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Netto", f"{calc['netto']:,.2f} PLN")
                m2.metric(f"VAT {calc['vat_rate']}%", f"{calc['vat_kwota']:,.2f} PLN")
                m3.metric("💰 BRUTTO", f"{calc['brutto']:,.2f} PLN")

                st.divider()
                st.markdown(f"↳ Materiały: **{calc['materialy_netto']:,.2f} PLN** netto")
                st.markdown(f"↳ Robocizna: **{calc['robocizna_netto']:,.2f} PLN** netto")

                if calc["mpp_required"]:
                    st.warning("⚠️ **MECHANIZM PODZIELONEJ PŁATNOŚCI** — kwota > 15 000 PLN brutto")

            # FAKTURA
            with res_col2:
                st.subheader("📄 Faktura VAT")
                st.text_area(
                    "Treść faktury (do wydruku/skopiowania)",
                    r["faktura_text"],
                    height=380,
                    key="invoice_display",
                )
                st.download_button(
                    "💾 Pobierz fakturę (.txt)",
                    r["faktura_text"],
                    file_name=f"faktura_{r['invoice_nr'].replace('/', '-')}.txt",
                    mime="text/plain",
                    type="secondary",
                )

            # Historia zleceń w sesji
            if "zlecenie_history" not in st.session_state:
                st.session_state.zlecenie_history = []
            existing = [h["nr"] for h in st.session_state.zlecenie_history]
            if r["invoice_nr"] not in existing:
                st.session_state.zlecenie_history.append({
                    "nr": r["invoice_nr"],
                    "typ": r["parse"]["typ_pracy"],
                    "brutto": r["calc"]["brutto"],
                    "data": r["invoice_date"],
                })

    # Historia zleceń
    history = st.session_state.get("zlecenie_history", [])
    if history:
        st.divider()
        st.subheader("📁 Historia zleceń w tej sesji")
        for h in reversed(history):
            st.markdown(f"• **{h['nr']}** — {h['typ'].title()} — {h['brutto']:,.2f} PLN brutto — {h['data']}")

# ─────────────────────────────────────────
# TAB 1: ASYSTENT BUDOWLANY
# ─────────────────────────────────────────
with tab1:

    st.header("Asystent Budowlany — Kosztorys i Porady")
    st.caption("Zapytaj o koszty materiałów, robocizny, lub popro o wycenę prac.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "construction_agent" not in st.session_state:
        try:
            st.session_state.construction_agent = ConstructionChatAgent()
        except Exception:
            st.session_state.construction_agent = None

    # Wyświetlenie historii czatu
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input użytkownika
    user_input = st.chat_input("Np. 'Ile kosztuje ocieplenie 200m2 styropianem 15cm?'")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analizuję..."):
                try:
                    agent = st.session_state.construction_agent or ConstructionChatAgent()
                    response = agent.chat(user_input)
                except Exception as e:
                    response = f"⚠️ Błąd agenta: {e}"
            st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

# ─────────────────────────────────────────
# TAB 2: AUDYT FAKTUR
# ─────────────────────────────────────────
with tab2:
    st.header("Audyt Faktur — Secure Audit")
    st.caption("Agent sprawdzi faktury zgodnie z przepisami **z roku ich wystawienia** (2018-2026). Oryginały są bezpieczne — praca na kopiach.")

    uploaded_audit_files = st.file_uploader(
        "Wgraj faktury do sprawdzenia (PDF, TXT, JPG)",
        accept_multiple_files=True,
        key="audit_upload",
        type=["pdf", "txt", "png", "jpg", "jpeg"],
    )

    prompt_override = st.text_input(
        "Dodatkowe instrukcje dla audytora (opcjonalnie)",
        placeholder="Np. 'Sprawdź stawkę VAT i kompletność danych'"
    )

    if st.button("🔍 Uruchom Audyt", key="audit_btn", type="primary") and uploaded_audit_files:
        temp_dir = os.path.join(_root, "temp_audit")
        os.makedirs(temp_dir, exist_ok=True)
        paths = []
        for uf in uploaded_audit_files:
            p = os.path.join(temp_dir, uf.name)
            with open(p, "wb") as f:
                f.write(uf.getbuffer())
            paths.append(p)

        audit_prompt = prompt_override or "Sprawdź faktury pod kątem błędów formalnych i rachunkowych"

        with st.spinner("🔒 Analizuję dokumenty (kopia bezpieczna)..."):
            try:
                agent = SecureAuditAgent()
                res = agent.process_audit(audit_prompt, paths)
                if res.get('status') == 'success':
                    st.success("✅ Audyt zakończony!")
                    st.text_area("Raport Audytora", res.get('report', ''), height=400)
                else:
                    st.error(f"Błąd: {res.get('message', 'Nieznany')}")
            except Exception as e:
                st.error(f"❌ Błąd audytu: {e}")
    elif st.button("🔍 Uruchom Audyt", key="audit_btn_disabled") if False else None:
        pass

    if not uploaded_audit_files:
        st.info("👆 Wgraj pliki aby uruchomić audyt.")

# ─────────────────────────────────────────
# TAB 3: WIRTUALNA KSIĘGOWA
# ─────────────────────────────────────────
with tab3:
    st.header("Wirtualna Księgowa")
    st.caption("Naucz AI jak wystawiasz faktury, a potem generuj nowe automatycznie.")

    col_learn, col_gen = st.columns(2, gap="large")

    with col_learn:
        st.subheader("1️⃣ Nauka Stylu")
        st.info("Wgraj przykładowe faktury. AI nauczy się Twojego stylu.", icon="📚")
        learn_files = st.file_uploader(
            "Wzory Faktur",
            accept_multiple_files=True,
            key="learn_upload",
            type=["pdf", "txt", "png", "jpg", "jpeg"],
        )

        if st.button("🎓 Ucz się z przykładów", key="learn_btn", type="primary") and learn_files:
            temp_dir = os.path.join(_root, "temp_learn")
            os.makedirs(temp_dir, exist_ok=True)
            paths = []
            for uf in learn_files:
                p = os.path.join(temp_dir, uf.name)
                with open(p, "wb") as f:
                    f.write(uf.getbuffer())
                paths.append(p)

            with st.spinner("Analizuję wzory (kopia bezpieczna)..."):
                try:
                    agent = AccountantAgent()
                    result = agent.learn_from_examples(paths)
                    st.success(result)
                except Exception as e:
                    st.error(f"❌ Błąd nauki: {e}")

    with col_gen:
        st.subheader("2️⃣ Wystaw Fakturę")
        st.info("Podaj dane — AI wystawi fakturę w Twoim stylu.", icon="📄")
        invoice_data = st.text_area(
            "Dane do faktury",
            height=200,
            placeholder="Np.\nSprzedawca: Firma Budowlanka Sp. z o.o.\nNabywca: Jan Kowalski, NIP: 123-456-78-90\nUsługa: Remont elewacji, 300m²\nKwota: 45000 PLN netto\nData: 2026-02-19",
        )

        if st.button("📄 Generuj Fakturę", key="gen_btn", type="primary") and invoice_data:
            with st.spinner("Piszę fakturę..."):
                try:
                    agent = AccountantAgent()
                    doc = agent.generate_invoice(invoice_data)
                    st.text_area("Gotowa Faktura", doc, height=400)
                    st.download_button("💾 Pobierz jako TXT", doc, "faktura.txt", "text/plain")
                except Exception as e:
                    st.error(f"❌ Błąd generowania: {e}")

# ─────────────────────────────────────────
# TAB 4: SYSTEM & SPRZĘT
# ─────────────────────────────────────────
with tab4:
    st.header("Diagnostyka Systemu")
    st.caption("Skanowanie sprzętu i dobór optymalnego profilu AI.")

    col_scan, col_info = st.columns([1, 2])

    with col_scan:
        if st.button("🔍 Skanuj Sprzęt", type="primary", key="hw_scan"):
            with st.spinner("Skanowanie..."):
                try:
                    hw = scan_hardware()
                    profile = determine_profile(hw)
                    st.session_state["hw_data"] = hw
                    st.session_state["hw_profile"] = profile
                except Exception as e:
                    st.error(f"Błąd skanowania: {e}")

        if st.button("⚙️ Regeneruj konfigurację", key="regen_config"):
            with st.spinner("Generowanie..."):
                try:
                    from synapsa.hardware import generate_env_file
                    prof = generate_env_file(".env")
                    st.success(f"✅ .env wygenerowany — Profil: {prof}")
                except Exception as e:
                    st.error(f"Błąd: {e}")

    with col_info:
        hw = st.session_state.get("hw_data")
        profile = st.session_state.get("hw_profile")

        if hw and profile:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("CPU", hw.get('cpu', {}).get('name', 'N/A')[:25])
                st.metric("Rdzenie", hw.get('cpu', {}).get('cores_logical', 'N/A'))
            with c2:
                st.metric("RAM", f"{hw.get('ram', {}).get('total_gb', 0)} GB")
                ram_free = hw.get('ram', {}).get('available_gb', 0)
                st.metric("RAM wolny", f"{ram_free} GB")
            with c3:
                gpu = hw.get('gpu', {})
                if gpu.get('available'):
                    st.metric("GPU", gpu.get('name', 'N/A')[:25])
                    st.metric("VRAM", f"{gpu.get('vram_total_gb', 0)} GB")
                else:
                    gpu_name_fallback = gpu.get('name', 'Brak dedykowanego')
                    st.metric("GPU", gpu_name_fallback[:30])
                    st.metric("VRAM", "N/A")

            st.divider()
            tier = profile.get('profile', 'UNKNOWN')
            desc = profile.get('description', '')
            colors = {
                "GOD_MODE": "🟢", "HIGH_PERFORMANCE": "🟢",
                "MID_PERFORMANCE": "🟡", "CPU_FALLBACK": "🟡",
                "CPU_WORKHORSE": "🟠", "CPU_STANDARD": "🟠",
                "POTATO_MODE": "🔴", "INCOMPATIBLE": "🔴",
            }
            icon = colors.get(tier, "⚪")
            st.metric("Profil AI", f"{icon} {tier}")
            st.info(desc)

            with st.expander("Szczegóły techniczne"):
                st.json(hw)
        else:
            st.info("Kliknij 'Skanuj Sprzęt' aby zobaczyć diagnostykę.")

    # Python info
    st.divider()
    st.subheader("Informacje o środowisku")
    import platform
    c1, c2, c3 = st.columns(3)
    c1.metric("Python", platform.python_version())
    c2.metric("System", platform.system())
    c3.metric("Architektura", platform.machine())

    # Library status
    st.subheader("Status bibliotek")
    libs = {
        "streamlit": "Streamlit (UI)",
        "torch": "PyTorch (AI Engine)",
        "transformers": "Transformers (Model Loading)",
        "peft": "PEFT (LoRA Adapters)",
        "bitsandbytes": "BitsAndBytes (4-bit Quantization)",
        "accelerate": "Accelerate (GPU Optimization)",
        "psutil": "PSUtil (Hardware Scan)",
    }
    lib_cols = st.columns(4)
    for idx, (lib, label) in enumerate(libs.items()):
        col = lib_cols[idx % 4]
        try:
            mod = __import__(lib)
            ver = getattr(mod, "__version__", "OK")
            col.success(f"✅ {label}\n`{ver}`")
        except ImportError:
            col.error(f"❌ {label}\nNie zainstalowany")
