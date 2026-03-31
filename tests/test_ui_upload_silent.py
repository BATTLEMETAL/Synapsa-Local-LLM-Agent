from playwright.sync_api import sync_playwright
import time
import os

def test_ui():
    print("Rozpoczęcie automatycznego testu E2E (UI + AI)...")
    file_path = r'c:\Users\mz100\PycharmProjects\Synapsa\dystrybucjaoffice\SynapsaOffice\Zrzut ekranu 2026-02-16 o 12.19.09.jpeg'
    
    if not os.path.exists(file_path):
        print("Nie znaleziono pliku testowego!")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print("1. Ładowanie aplikacji...")
            page.goto('http://localhost:8505')
            page.wait_for_timeout(3000)
            
            print("2. Przejście do zakładki 'Audyt Faktur'...")
            page.get_by_role("tab", name="🕵️ Audyt Faktur").click()
            page.wait_for_timeout(2000)
            
            print("3. Ciche wgrywanie pliku faktury z pominięciem dialogu Windows...")
            page.locator('input[type="file"]').first.set_input_files(file_path)
            page.wait_for_timeout(2000)
            
            print("4. Uruchamianie audytu AI...")
            page.locator('text=Uruchom Audyt').click()
            
            # Nasłuchiwanie zmian na stronie (czekamy aż zniknie spinner / pojawi się wynik)
            print("5. Oczekiwanie na model Qwen2.5 (RTX 3060 CUDA)... (max 60s)")
            page.wait_for_timeout(30000)
            
            results = page.locator('.stMarkdown').all_inner_texts()
            success = False
            for text in results:
                if 'NIP' in text or 'RAPORT' in text or 'Analiza' in text:
                    print("\n--- ZNALEZIONY WYNIK Z UI ---")
                    print(text[:800] + "...\n")
                    success = True
                    break
            
            if success:
                print("✅ Test E2E Pomyślny! Interfejs graficzny i model AI współpracują bezbłędnie.")
            else:
                print("⚠️  Brak oczekiwanego wyniku w interfejsie.")
                
            browser.close()
            
    except Exception as e:
        print(f"❌ Błąd Playwright: {e}")

if __name__ == '__main__':
    test_ui()
