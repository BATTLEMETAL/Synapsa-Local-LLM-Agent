import os
import json
import difflib
import google.generativeai as genai
from core.engine import SynapsaEngine
from config import settings


class AuditorAgent:
    """
    Agent Audytora Hybrydowego.
    Łączy lokalną wiedzę modelu Qwen z ekspercką wiedzą Google Gemini.
    Implementacja na podstawie Twoich plików: Audytor_Hybrid.py i Audytor_Ultimate.py.
    """

    def __init__(self):
        # Inicjalizacja silnika lokalnego (Singleton - nie ładuje się drugi raz)
        self.engine = SynapsaEngine()

        # Konfiguracja Sędziego Gemini (Google Cloud)
        genai.configure(api_key=settings.GEMINI_KEY)
        self.generation_config = {
            "temperature": 0.1,  # Niska temperatura dla precyzji inżynierskiej
            "top_p": 0.95,
            "max_output_tokens": 8192,
        }
        # Wybieramy model Flash dla szybkości, zgodnie z Twoim skryptem Hybrid
        self.judge_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            generation_config=self.generation_config
        )

    def _show_diff(self, old_code, new_code, label="ZMIANY"):
        """Generuje raport różnic w stylu unified diff."""
        diff = difflib.unified_diff(
            old_code.splitlines(),
            new_code.splitlines(),
            fromfile='Oryginał',
            tofile='Poprawiony',
            lineterm=''
        )
        return "\n".join(list(diff))

    def _save_lesson(self, original, final, filename):
        """
        Zapisuje parę (Oryginał, Poprawka) do bazy wiedzy.
        To paliwo dla skryptu Trener.py.
        """
        dataset_path = "moj_finalny_dataset.jsonl"
        lesson = {
            "instruction": f"Fix bugs, optimize performance and apply clean code principles in this file: {filename}",
            "input": original,
            "output": final
        }
        try:
            with open(dataset_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(lesson, ensure_ascii=False) + "\n")
            print(f"🎓 Wiedza zapisana w {dataset_path} (Źródło: Gemini-Enhanced)")
        except Exception as e:
            print(f"⚠️ Błąd zapisu lekcji: {e}")

    def run_full_audit(self, code, filename="code_snippet.py"):
        """
        Pełna procedura audytu:
        1. Lokalny model generuje poprawkę.
        2. Gemini weryfikuje i ewentualnie ulepsza.
        3. Generowanie raportu diff.
        """
        print(f"🕵️  Rozpoczynam audyt pliku: {filename}")

        # --- ETAP 1: Lokalna Analiza ---
        local_prompt = f"""
        Act as a Senior Software Engineer. Analyze and fix the following code.
        Focus on: Security (SQLi, XSS), Threading issues, and Clean Code.

        CODE:
        {code}
        """
        local_fix = self.engine.smart_generate(local_prompt)

        # --- ETAP 2: Weryfikacja przez Mistrza (Gemini) ---
        print("✨ Weryfikacja przez Sędziego Gemini...")
        judge_prompt = f"""
        Act as a Principal Software Engineer and Security Auditor.

        TASK: Compare the ORIGINAL CODE with the PROPOSED FIX.

        ORIGINAL CODE:
        {code}

        PROPOSED FIX (by a Junior AI):
        {local_fix}

        INSTRUCTIONS:
        1. Check for logic bugs, hallucinations, security flaws, and best practices.
        2. If the Proposed Fix is PERFECT, return it exactly as is.
        3. If the Proposed Fix has ANY issues or can be optimized, write the BEST POSSIBLE version.

        OUTPUT:
        Return ONLY the final, clean Code block inside markdown backticks.
        """

        try:
            response = self.judge_model.generate_content(judge_prompt)
            # Używamy tej samej logiki czyszczenia co w silniku, aby wyciągnąć kod z markdown
            _, final_code = self.engine.clean_output(response.text)
        except Exception as e:
            print(f"❌ Błąd Gemini: {e}. Zostaję przy poprawce lokalnej.")
            final_code = local_fix

        # --- ETAP 3: Analiza różnic i zapis ---
        diff_report = self._show_diff(code, final_code)

        # Automatyczne douczanie (Lekcja)
        if final_code.strip() != code.strip():
            self._save_lesson(code, final_code, filename)

        return {
            "status": "success",
            "filename": filename,
            "original_code": code,
            "final_code": final_code,
            "diff": diff_report,
            "improved_by_gemini": final_code.strip() != local_fix.strip()
        }