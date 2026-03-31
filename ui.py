import streamlit as st
import requests

st.set_page_config(page_title="Synapsa AI Platform", layout="wide")

st.title("🧠 Synapsa AI: Autonomous Engineering Framework")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Terminal Operacyjny")
    code_input = st.text_area("Wklej kod do audytu:", height=400)
    if st.button("Uruchom Audyt"):
        with st.spinner("Synapsa myśli..."):
            response = requests.post("http://localhost:8000/v1/audit", json={"code": code_input, "filename": "test.py"})
            st.json(response.json())

with col2:
    st.header("Statystyki Systemu")
    st.metric("Model", "Qwen 2.5 Coder 7B")
    st.metric("Wiedza (Dataset)", "1,240 rekordów")
    st.progress(85, text="Zajętość VRAM (10.2 / 12 GB)")