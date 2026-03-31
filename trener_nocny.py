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


# --- MOCKOWANIE TRITONA ---
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
    dummy_name = "triton_dummy_night.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()

# ==========================================
# 2. PARAMETRY TRENINGU (REASONING MODE)
# ==========================================
DATASET_FILE = "moj_finalny_dataset_reasoning.jsonl"
OUTPUT_DIR = "moje_ai_adaptery"
MODEL_NAME = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"

# Zwiększamy kontekst, bo Reasoning + Code zajmuje dużo tokenów
MAX_SEQ_LENGTH = 2048


def train_brain_night_mode():
    torch.cuda.empty_cache()
    print(f"\n🌙  Start Trenera (Reasoning Mode - Chain of Thought)...")
    print(f"🧠  Cel: Nauczyć model MYŚLEĆ przed kodowaniem.")

    if not os.path.exists(DATASET_FILE):
        print(f"❌ Brak pliku: {DATASET_FILE}")
        return

    # 1. Ładowanie Modelu
    print(f"📥 Ładowanie modelu bazy...")
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

    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()
    model.config.use_cache = False

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Konfiguracja LoRA
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

    # 3. Dane
    try:
        dataset = load_dataset("json", data_files=DATASET_FILE, split="train")
        print(f"📚 Załadowano {len(dataset)} przykładów.")
    except Exception as e:
        print(f"❌ Błąd danych: {e}")
        return

    def formatting_func(example):
        instr = example["instruction"]
        output = example["output"]
        # output zawiera: <thinking>...</thinking>\nCode...

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

    # 4. Trening NOCNY
    print(f"🔥 Rozpoczynam głęboki trening...")

    trainer = Trainer(
        model=model,
        train_dataset=tokenized_dataset,
        args=TrainingArguments(
            output_dir=OUTPUT_DIR,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            optim="paged_adamw_8bit",
            warmup_steps=20,
            num_train_epochs=3,  # 3 epoki dla utrwalenia wzorca myślenia
            learning_rate=2e-4,
            fp16=True,
            logging_steps=1,
            save_strategy="epoch",
            dataloader_num_workers=0,
        ),
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    trainer.train()

    # 5. Zapis
    print(f"💾 Zapisywanie Mózgu do '{OUTPUT_DIR}'...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, "adapter_config.json"), "r+") as f:
        data = json.load(f)
        data["base_model_name_or_path"] = MODEL_NAME
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    print("\n✅ TRENING ZAKOŃCZONY! Model powinien teraz używać <thinking>.")


if __name__ == "__main__":
    try:
        train_brain_night_mode()
    except Exception as e:
        print(f"❌ Błąd: {e}")
        input("Enter...")