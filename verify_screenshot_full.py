
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyScreenshot")

from synapsa.agents.office_agent import SecureAuditAgent

def test_screenshot():
    # Path to the screenshot
    base_dir = r"C:\Users\mz100\PycharmProjects\Synapsa\dystrybucjaoffice\SynapsaOffice"
    filename = "Zrzut ekranu 2026-02-16 o 12.19.09.jpeg"
    file_path = os.path.join(base_dir, filename)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print(f"🚀 Initializing Agent and Engine (loading model...)...")
    try:
        agent = SecureAuditAgent() # This loads the model!
    except Exception as e:
        print(f"❌ Failed to load engine: {e}")
        return

    print(f"📸 Processing file: {filename}")
    print("This may take a moment due to OCR and LLM generation...")
    
    prompt = "Przeanalizuj tę fakturę pod kątem poprawności danych (NIP, Daty, Kwoty)."
    
    try:
        result = agent.process_audit(prompt, [file_path])
        
        print("\n" + "="*50)
        print("RESULT:")
        print("="*50)
        
        if result['status'] == 'success':
            print("✅ SUKCES!")
            print("Raport:")
            print(result['report'])
            print(f"Workspace: {result['workspace']}")
        else:
            print("❌ BŁĄD!")
            print(f"Message: {result['message']}")
            print(f"Last Error: {result['last_error']}")
            
    except Exception as e:
        print(f"❌ Runtime Exception: {e}")

if __name__ == "__main__":
    test_screenshot()
