import os
import sys
import torch
import warnings
import importlib.util
import site
import json
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)

# ==========================================
# 1. KONFIGURACJA SYSTEMOWA (Windows Fixes)
# ==========================================
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"

warnings.filterwarnings("ignore")


# --- MOCKOWANIE TRITONA (Żeby PEFT nie płakał) ---
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
    dummy_name = "triton_dummy_train.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()

# ==========================================
# 2. PARAMETRY (LITE MODE - SZYBKI TRENING)
# ==========================================
DATASET_FILE = "moj_finalny_dataset.jsonl"
OUTPUT_DIR = "moje_ai_adaptery"
MODEL_NAME = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"

# ZMIANA: Zmniejszono z 1024 na 512, aby zmieścić się w VRAM RTX 3060
MAX_SEQ_LENGTH = 512


def train_brain():
    # 0. Start
    torch.cuda.empty_cache()
    print(f"\n🏋️  Start Trenera (Lite Mode - RTX 3060 Friendly)...")

    if not os.path.exists(DATASET_FILE):
        print(f"❌ Brak pliku '{DATASET_FILE}'. Najpierw użyj Audytora i zapisz jakieś poprawki!")
        return

    # Sprawdzamy rozmiar datasetu
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        dataset_size = len(lines)

    if dataset_size == 0:
        print("⚠️ Dataset jest pusty.")
        return

    print(f"📚 Liczba lekcji do przyswojenia: {dataset_size}")

    # 1. Ładowanie Modelu (BitsAndBytes - 4bit)
    print(f"📥 Ładowanie modelu bazy: {MODEL_NAME}...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )

    # Przygotowanie do treningu w 4-bitach
    model = prepare_model_for_kbit_training(model)

    # --- FIX: Wymuszenie checkpointingu i wyłączenie cache ---
    model.gradient_checkpointing_enable()
    model.config.use_cache = False
    # ---------------------------------------------------------

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token  # Fix dla Qwen
    tokenizer.padding_side = "right"  # Fix dla treningu

    # 2. Konfiguracja LoRA (Adaptery)
    peft_config = LoraConfig(
        r=16,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 3. Przygotowanie Danych
    print(f"🛠️  Przetwarzanie danych...")
    dataset = load_dataset("json", data_files=DATASET_FILE, split="train")

    def formatting_func(example):
        inputs = example.get("input", "")
        instr = example["instruction"]
        output = example["output"]

        # Przycinamy tekst, żeby nie przekroczył limitu
        if inputs and str(inputs).strip():
            text = f"### Instruction:\n{instr}\n\n### Input:\n{inputs}\n\n### Response:\n{output}<|endoftext|>"
        else:
            text = f"### Instruction:\n{instr}\n\n### Response:\n{output}<|endoftext|>"

        tokenized = tokenizer(
            text,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    tokenized_dataset = dataset.map(formatting_func, remove_columns=dataset.column_names)

    # 4. Trening
    # Zamiast wyliczać kroki ręcznie, ustawiamy 1 Epokę.
    print(f"🔥 Rozpoczynam trening (1 Epoka)...")

    trainer = Trainer(
        model=model,
        train_dataset=tokenized_dataset,
        args=TrainingArguments(
            output_dir=OUTPUT_DIR,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=2,  # ZMNIEJSZONO z 4 na 2 (Częstsze czyszczenie VRAM)
            warmup_steps=10,
            num_train_epochs=1,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=5,                # Częstsze logi
            optim="adamw_8bit",             # ZMIANA KLUCZOWA (Oszczędza pamięć)
            save_strategy="epoch",
            dataloader_num_workers=0,
        ),
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    trainer.train()

    # 5. Zapisywanie
    print(f"💾 Zapisywanie do '{OUTPUT_DIR}'...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, "adapter_config.json"), "r+") as f:
        data = json.load(f)
        data["base_model_name_or_path"] = MODEL_NAME
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    print("\n✅ TRENING ZAKOŃCZONY SUKCESEM!")
    print("   Uruchom 'Audytor.py' - model automatycznie załaduje nową wiedzę.")


if __name__ == "__main__":
    try:
        train_brain()
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        input("Enter...")