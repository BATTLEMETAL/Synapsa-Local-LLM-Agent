
import requests
import json
import time

def assess_ai():
    print("🧠 Assessing Synapsa AI Intelligence Level...")
    
    prompt = """You are a Principal Software Architect.
    Design a robust, scalable architecture for a 'Real-Time Stock Trading Platform'.
    
    Requirements:
    1. Handle high throughput order ingestion.
    2. Maintain strict ACID compliance for balances.
    3. Provide real-time data feeds via WebSockets.
    
    Output Format:
    1. Architectural reasoning (Chain of Thought).
    2. High-level component diagram (text/mermaid).
    3. Python code snippet for the core Order Matching Engine.
    """
    
    url = "http://127.0.0.1:8000/api/v1/generate"
    
    try:
        start_time = time.time()
        print("⏳ Sending complex architectural request to API...")
        
        response = requests.post(
            url, 
            json={"prompt": prompt, "temperature": 0.2, "max_tokens": 2000},
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            duration = time.time() - start_time
            
            raw_output = data.get("code") or data.get("raw") or ""
            thinking = data.get("thinking", "")
            
            print(f"\n✅ Response received in {duration:.2f}s")
            
            # Assessment Logic
            score = 0
            level = "Junior Developer"
            
            if len(raw_output) > 500: score += 1
            if "class " in raw_output: score += 1
            if "def " in raw_output: score += 1
            if "async" in raw_output or "await" in raw_output: score += 1  # Modern python
            if "try" in raw_output and "except" in raw_output: score += 1  # Error handling
            if "<thinking>" in raw_output or thinking: score += 3  # Reasoning capability (High value!)
            if "Redis" in raw_output or "Kafka" in raw_output or "PostgreSQL" in raw_output: score += 1 # System design awareness
            
            if score >= 8:
                level = "💀 GIGA-CHAD ARCHITECT (Senior+)"
            elif score >= 5:
                level = "Senior Developer"
            elif score >= 3:
                level = "Mid-Level Developer"
                
            print(f"\n🏆 AI Degree Assessment: {level}")
            print(f"📊 Quality Score: {score}/10")
            print(f"🧠 Reasoning Detected: {'YES' if (thinking or '<thinking>' in raw_output) else 'NO'}")
            
            print("\n--- Model Output Snippet ---")
            print(raw_output[:500] + "...\n")
            if thinking:
                print("--- Reasoning Snippet ---")
                print(thinking[:300] + "...")
                
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Is main.py running?")

if __name__ == "__main__":
    assess_ai()
