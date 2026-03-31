
import sys
import os

sys.path.append(os.getcwd())
try:
    import synapsa.compat # Mock Triton etc.
    print("🚀 Testing Unsloth Import...")
    from unsloth import FastLanguageModel
    print(f"✅ Unsloth imported version: {FastLanguageModel}")
    
    print("⏳ Testing FastLanguageModel.from_pretrained...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit",
        max_seq_length=2048,
        load_in_4bit=True,
    )
    print("✅ Model loaded successfully!")

except Exception as e:
    print(f"❌ Unsloth Error: {e}")
    import traceback
    traceback.print_exc()
