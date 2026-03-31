import os
import json
import time
import random
import torch
import warnings
import sys
import importlib.util
import subprocess  # Do uruchamiania trenera
from groq import Groq
import google.generativeai as genai
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# 1. KONFIGURACJA API I CELÓW
# ==========================================

# ILE LEKCJI MA ZROBIĆ PRZEZ NOC?
# 400 lekcji to optymalna liczba na jedną noc (uwzględniając limity API).
TARGET_LESSONS = 400

# Klucz GROQ — ustaw jako zmienną środowiskową: export GROQ_API_KEY=...
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Klucz Gemini — ustaw jako zmienną środowiskową: export GEMINI_API_KEY=...
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

ADAPTER_PATH = "moje_ai_adaptery"
DATASET_FILE = "moj_finalny_dataset.jsonl"
TRAINER_SCRIPT = "trener.py"

TOPICS = [
    "Advanced Python Asyncio Patterns", "Secure REST API Architecture",
    "Solid Principles in Real Life", "Design Patterns (Factory, Singleton, Observer)",
    "Database Transaction Atomicity", "Microservices Communication",
    "Secure Authentication Flows (OAuth2/JWT)", "Memory Management in High-Load Systems",
    "Dependency Injection Containers", "Writing Scalable Dockerfiles",
    "Kotlin Coroutines Deep Dive", "C# Entity Framework Performance",
    "React Hooks Optimization", "Cybersecurity: XSS & SQLi Prevention"
]

os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
warnings.filterwarnings("ignore")


class Colors:
    HEADER = '\033[95m'
    GROQ = '\033[92m'  # Zielony
    GEMINI = '\033[96m'  # Cyan
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    LEVEL = '\033[96m'


# ==========================================
# 2. MOCK TRITON
# ==========================================
def setup_triton_mock():
    dummy_code = '''
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
_mock = UniversalMock()
def cdiv(x, y): return (x + y - 1) // y
def next_power_of_2(n): return 1
def autotune(*args, **kwargs): return lambda fn: fn
def jit(*args, **kwargs): return lambda fn: fn
Config = _mock
compile = _mock
'''
    dummy_name = "triton_dummy_sensei.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()

# ==========================================
# 3. AUTO-KONFIGURACJA SILNIKÓW
# ==========================================

# --- A. Konfiguracja GROQ ---
groq_client = None
if "gsk_" in GROQ_API_KEY and "TU_WKLEJ" not in GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"{Colors.GROQ}✅ Wykryto klucz GROQ. Używam modelu Llama-3.3-70b (Ultra Szybki).{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Błąd klucza Groq: {e}{Colors.ENDC}")
else:
    print(f"{Colors.WARNING}⚠️ Brak klucza Groq. Działam tylko na Gemini.{Colors.ENDC}")

# --- B. Konfiguracja GEMINI ---
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = None

print(f"{Colors.GEMINI}📡 Skanuję Twoje konto Google...{Colors.ENDC}")
try:
    all_models = genai.list_models()
    available_names = [m.name.replace("models/", "") for m in all_models if
                       'generateContent' in m.supported_generation_methods]

    priorities = [
        'gemini-flash-latest', 'gemini-2.0-flash', 'gemini-2.5-flash',
        'gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-pro'
    ]

    selected_name = None
    for p in priorities:
        if p in available_names:
            selected_name = p
            break

    if not selected_name and available_names: selected_name = available_names[0]

    if selected_name:
        print(f"{Colors.GEMINI}✅ Znaleziono Gemini: {Colors.BOLD}{selected_name}{Colors.ENDC}")
        gemini_model = genai.GenerativeModel(selected_name,
                                             generation_config={"response_mime_type": "application/json"})
    else:
        print(f"{Colors.FAIL}❌ Krytyczny błąd: Brak dostępu do modeli Gemini.{Colors.ENDC}")

except Exception as e:
    print(f"{Colors.FAIL}❌ Błąd połączenia z Google: {e}{Colors.ENDC}")


def ask_teacher_json(prompt):
    """Hybrydowe zapytanie: Groq -> Failover -> Gemini"""
    # 1. GROQ (Priorytet)
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a coding expert. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, max_tokens=2048, response_format={"type": "json_object"}
            )
            print(f"{Colors.GROQ}⚡ [Groq] Generuje...{Colors.ENDC}", end="\r")
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            pass

    # 2. GEMINI (Zapas)
    if gemini_model:
        try:
            print(f"{Colors.GEMINI}💎 [Gemini] Przejmuje zadanie...{Colors.ENDC}", end="\r")
            response = gemini_model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.endswith("```"): text = text[:-3]
            return json.loads(text)
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                return "LIMIT_HIT"
            pass

    return "LIMIT_HIT"


# ==========================================
# 4. INICJALIZACJA UCZNIA
# ==========================================
print(f"{Colors.HEADER}⏳ Budzenie Ucznia (Local AI)...{Colors.ENDC}")
try:
    base_name = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"
    if os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json")):
        with open(os.path.join(ADAPTER_PATH, "adapter_config.json"), 'r') as f:
            base_name = json.load(f).get("base_model_name_or_path", base_name)

    bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16,
                                    bnb_4bit_use_double_quant=True)
    student_model = AutoModelForCausalLM.from_pretrained(base_name, quantization_config=bnb_config, device_map="auto",
                                                         trust_remote_code=True)
    student_tokenizer = AutoTokenizer.from_pretrained(base_name, trust_remote_code=True)

    if os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json")):
        print(f"{Colors.BLUE}🔗 Podłączanie adapterów LoRA...{Colors.ENDC}")
        student_model = PeftModel.from_pretrained(student_model, ADAPTER_PATH)

    student_model.eval()
    print(f"{Colors.GREEN}✅ Uczeń gotowy.{Colors.ENDC}")
except Exception as e:
    print(f"{Colors.FAIL}❌ Błąd ucznia: {e}{Colors.ENDC}");
    sys.exit(1)


def ask_student(prompt):
    formatted = f"### Instruction:\nYou are a Senior Software Architect. Create a complete, robust, and professional solution.\n{prompt}\n\n### Response:\n"
    inputs = student_tokenizer([formatted], return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = student_model.generate(**inputs, max_new_tokens=768, temperature=0.2, do_sample=True)
    decoded = student_tokenizer.decode(out[0], skip_special_tokens=True)
    return decoded.split("### Response:")[-1].strip() if "### Response:" in decoded else decoded.strip()


# ==========================================
# 5. PĘTLA TRENINGOWA (NIGHT MODE)
# ==========================================
def training_session():
    print(f"{Colors.HEADER}🌙 Sensei: Tryb Nocny (Night Ops).{Colors.ENDC}")
    print(f"🎯 CEL: Zebrać {Colors.BOLD}{TARGET_LESSONS}{Colors.ENDC} lekcji, a potem uruchomić trening.")

    current_difficulty = 1
    max_difficulty = 5
    collected_samples = 0
    milestone_step = TARGET_LESSONS // 4  # Krok co 25%

    # Główna pętla - działa dopóki nie osiągniemy celu
    while collected_samples < TARGET_LESSONS:
        topic = random.choice(TOPICS)

        # Obliczanie postępu
        progress_pct = int((collected_samples / TARGET_LESSONS) * 100)

        desc = f"Level {current_difficulty}/5"
        print(
            f"\n{Colors.BOLD}📚 Lekcja {collected_samples + 1}/{TARGET_LESSONS} ({progress_pct}%): {topic}{Colors.ENDC}")
        print(f"{Colors.LEVEL}⚡ {desc}{Colors.ENDC}")

        # RAPORT CO 25%
        if collected_samples > 0 and collected_samples % milestone_step == 0:
            print(
                f"\n🔔 {Colors.HEADER}OSIĄGNIĘTO {progress_pct}% CELU! ({collected_samples} lekcji). System stabilny.{Colors.ENDC}\n")

        # 1. GENEROWANIE
        print("   Sensei przygotowuje wyzwanie...")
        scenario = ask_teacher_json(f"""
            Generate a coding challenge about '{topic}'.
            DIFFICULTY LEVEL: {current_difficulty} out of 5.
            Description: {desc}.
            Output JSON keys: "instruction", "bad_code", "correct_code".
            "correct_code" must be the Perfect Solution (Gold Standard).
        """)

        # CRITICAL FAILOVER CHECK
        if scenario == "LIMIT_HIT":
            print(f"\n{Colors.FAIL}🛑 LIMITY WYCZERPANE (GROQ + GEMINI).{Colors.ENDC}")
            trigger_auto_train(collected_samples)
            break

        if not isinstance(scenario, dict):
            time.sleep(2);
            continue

        instr = scenario.get('instruction')
        bad_code = scenario.get('bad_code')
        gold_code = scenario.get('correct_code')

        # 2. ROZWIĄZYWANIE
        print("   Uczeń pracuje...")
        student_answer = ask_student(f"{instr}\nContext:\n{bad_code}")

        # 3. OCENA
        print("   Sensei sprawdza...")
        verdict = ask_teacher_json(f"""
            Role: Strict Technical Lead. Difficulty: {current_difficulty}/5.
            Compare STUDENT vs GOLD STANDARD for: "{instr}".
            Criteria: Correctness, Security, Completeness, Professionalism.
            Output JSON keys: "is_correct" (boolean), "reason" (string).
            STUDENT ANSWER: {student_answer}
            GOLD STANDARD: {gold_code}
        """)

        # CRITICAL FAILOVER CHECK
        if verdict == "LIMIT_HIT":
            print(f"{Colors.WARNING}⚠️ Limity padły podczas oceny. Zapisuję ostatni Gold Standard...{Colors.ENDC}")
            save_lesson(instr, bad_code, gold_code, "EMERGENCY_SAVE")
            trigger_auto_train(collected_samples + 1)
            break

        if not isinstance(verdict, dict):
            time.sleep(2);
            continue

        if verdict.get('is_correct'):
            print(f"{Colors.GREEN}   ✅ Zaliczone! ({verdict.get('reason')[:50]}...){Colors.ENDC}")
            if current_difficulty < max_difficulty:
                current_difficulty += 1
                print(f"{Colors.LEVEL}   📈 Level Up! -> {current_difficulty}.{Colors.ENDC}")
            else:
                print(f"{Colors.LEVEL}   👑 Max Level!{Colors.ENDC}")
                # Na max levelu zapisujemy rzadziej (tylko wybitne), żeby nie przeuczyć
                if random.random() > 0.7:
                    save_lesson(instr, bad_code, gold_code, "ARCHITECT_PATTERN")
                    collected_samples += 1
        else:
            print(f"{Colors.FAIL}   ❌ Porażka. ({verdict.get('reason')[:50]}...){Colors.ENDC}")
            print(f"{Colors.BLUE}   💾 Zapisuję wiedzę...{Colors.ENDC}")
            save_lesson(instr, bad_code, gold_code, "KNOWLEDGE_GAP")
            collected_samples += 1

            if current_difficulty > 1:
                current_difficulty -= 1
                print(f"{Colors.WARNING}   📉 Level Down. -> {current_difficulty}.{Colors.ENDC}")

        # Pauza dla API
        print("   ⏳ (2s)...")
        time.sleep(2)

    # KONIEC PĘTLI
    print(f"\n🏁 {Colors.HEADER}CEL OSIĄGNIĘTY ({TARGET_LESSONS} lekcji).{Colors.ENDC}")
    trigger_auto_train(collected_samples)


def trigger_auto_train(samples_count):
    """Zamyka Senseia i odpala Trenera."""
    print(f"\n{Colors.HEADER}🚀 URUCHAMIAM PROCEDURĘ AUTO-TRENINGU{Colors.ENDC}")
    print(f"📊 Zebrano {samples_count} nowych lekcji.")

    if samples_count == 0:
        print("⚠️ Brak nowych danych. Trening anulowany.")
        return

    print("⏳ Zwalniam pamięć GPU przed treningiem...")
    torch.cuda.empty_cache()

    # Uruchomienie Trenera w nowym procesie
    try:
        print(f"🔄 Startuję: {TRAINER_SCRIPT}...")
        # Check=True sprawi, że jeśli trener się wywali, dostaniemy info
        subprocess.run([sys.executable, TRAINER_SCRIPT], check=True)
        print(f"\n{Colors.GREEN}✅ Cykl Nocny Zakończony Sukcesem!{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Błąd podczas uruchamiania trenera: {e}{Colors.ENDC}")


def save_lesson(instr, inp, out, source_tag):
    # ZABEZPIECZENIE TYPÓW (Fix dla ArrowInvalid)
    if isinstance(inp, (dict, list)): inp = json.dumps(inp, ensure_ascii=False)
    if isinstance(out, (dict, list)): out = json.dumps(out, ensure_ascii=False)

    lesson = {
        "instruction": str(f"[{source_tag}] {instr}"),
        "input": str(inp) if inp else "",
        "output": str(out) if out else ""
    }
    with open(DATASET_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(lesson, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        training_session()
    except KeyboardInterrupt:
        print(f"\n{Colors.HEADER}🛑 Zatrzymano manualnie. Uruchamiam trening na zebranych danych...{Colors.ENDC}")
        # Manualne przerwanie też odpala trenera, jeśli zebrano jakiekolwiek dane
        # Podajemy 1, żeby funkcja ruszyła (trener i tak sprawdzi plik)
        trigger_auto_train(1)