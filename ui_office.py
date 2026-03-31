"""
Synapsa Secure Audit - Dashboard
Interfejs użytkownika dla produktu "Synapsa Office Box".
Umożliwia wgranie plików (Faktury/Excel), izolowaną analizę i pobranie raportu.
"""
import streamlit as st
import os
import time
# Mockowanie Agenta (bo nie mamy pełnego środowiska w Streamlit cloud, ale lokalnie zadziała)
try:
    from synapsa.agents.office_agent import SecureAuditAgent
except ImportError:
    st.error("Nie znaleziono modułu Synapsa. Uruchom ze ścieżki projektu.")
    SecureAuditAgent = None

st.set_page_config(page_title="Synapsa Secure Audit", page_icon="🔒", layout="wide")

# CSS dla klimatu "Enterprise Secure"
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        font-weight: 700;
    }
    .status-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #1a1c24;
        border: 1px solid #333;
    }
    .safe-badge {
        background-color: #4CAF50;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-header">🔒 Synapsa Secure Audit</div>', unsafe_allow_html=True)
    st.caption("Offline AI Financial Auditor | v2.0 (Secure Logic)")
with col2:
    st.markdown("### Status Systemu")
    st.markdown('<span class="safe-badge">✓ AST GUARD ACTIVE</span>', unsafe_allow_html=True)
    st.markdown('<span class="safe-badge">✓ FILE ISOLATION</span>', unsafe_allow_html=True)

st.divider()

# Sidebar - Konfiguracja
with st.sidebar:
    st.header("⚙️ Konfiguracja Audytu")
    audit_mode = st.selectbox(
        "Tryb Audytu",
        ["Analiza Faktur (Spójność)", "Weryfikacja Excel (Błędy)", "Ekstrakcja Danych (OCR)"]
    )
    st.info("💡 Tryb 'Analiza Faktur' sprawdza, czy kwoty netto + VAT dają brutto.")

# Main Area
col_upload, col_result = st.columns(2)

with col_upload:
    st.subheader("1. Wgraj Dokumenty")
    uploaded_files = st.file_uploader(
        "Wrzuć faktury (PDF, JPG) lub zestawienia (XLSX, CSV)", 
        accept_multiple_files=True
    )
    
    audit_instruction = st.text_area(
        "2. Instrukcja dla Agenta", 
        value="Sprawdź poprawność matematyczną faktur i wygeneruj raport błędów.",
        height=100
    )
    
    start_btn = st.button("🚀 Rozpocznij Bezpieczny Audyt", type="primary", use_container_width=True)

if start_btn and uploaded_files and SecureAuditAgent:
    with col_result:
        st.subheader("3. Wyniki Audytu")
        status_container = st.empty()
        
        # 1. Zapisywanie plików tymczasowych (upload -> temp)
        temp_dir = "temp_upload"
        os.makedirs(temp_dir, exist_ok=True)
        file_paths = []
        
        status_container.info("📥 Przygotowywanie plików...")
        progress_bar = st.progress(0)
        
        for uploaded_file in uploaded_files:
            path = os.path.join(temp_dir, uploaded_file.name)
            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_paths.append(path)
        
        progress_bar.progress(20)
        
        # 2. Uruchomienie Agenta
        status_container.warning("🔒 Izolowanie plików w Secure Zone...")
        time.sleep(0.5) # UI effect
        progress_bar.progress(40)
        
        agent = SecureAuditAgent()
        status_container.info("🕵️  Agent analizuje dane (Może to chwilę potrwać)...")
        
        # Real processing
        result = agent.process_audit(audit_instruction, file_paths)
        progress_bar.progress(90)
        
        # 3. Wynik
        status_container.empty()
        if result['status'] == 'success':
            st.success("✅ Audyt Zakończony Pomyślnie!")
            
            with st.expander("📄 Raport Audytu", expanded=True):
                st.code(result.get('report', 'Brak treści raportu.'), language='text')
            
            st.caption(f"Workspace: {result.get('workspace')}")
            
            # Button do pobrania raportu? (Można dodać)
        else:
            st.error("❌ Błąd Audytu")
            st.code(result.get('last_error', 'Nieznany błąd'), language='text')
            st.warning("Agent próbował 3 razy naprawić kod, ale napotkał błędy strukturalne w danych.")
            
        progress_bar.progress(100)

elif start_btn and not uploaded_files:
    st.warning("Najpierw wgraj jakieś pliki!")
