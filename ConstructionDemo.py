"""
DEMO: Synapsa Budowlanka Edition
Skrypt pokazowy dla klienta z branży budowlanej.
"""
import os
import sys
import time

# Dodajemy ścieżkę do projektu
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from synapsa.agents.office_agent import SecureAuditAgent
from synapsa.agents.construction_agent import ConstructionChatAgent

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def create_mock_invoices():
    """Tworzy przykładowe faktury do demo."""
    os.makedirs("demo_docs", exist_ok=True)
    
    # 1. Faktura Poprawna
    with open("demo_docs/faktura_ok.txt", "w", encoding="utf-8") as f:
        f.write("""
        FAKTURA VAT 01/2026
        Sprzedawca: Hurtownia "BUD-MAX", NIP: 123-456-78-19
        Nabywca: Firma Budowlana "SOLIDNA ROBOTA"
        
        Pozycje:
        1. Cement 25kg x 10 worków. Netto: 200.00 PLN. VAT (23%): 46.00 PLN. Brutto: 246.00 PLN
        2. Wapno hydratyzowane x 5. Netto: 100.00 PLN. VAT (23%): 23.00 PLN. Brutto: 123.00 PLN
        
        RAZEM:
        Netto: 300.00 PLN
        VAT: 69.00 PLN
        Brutto: 369.00 PLN
        """)
        
    # 2. Faktura z Błędem
    with open("demo_docs/faktura_error.txt", "w", encoding="utf-8") as f:
        f.write("""
        FAKTURA VAT 02/2026 (BŁĘDNA)
        Sprzedawca: Janusz-Bud sp. z o.o., NIP: 999-888-77-66
        
        Pozycje:
        1. Usługa remontowa (Gładzie). Netto: 1000.00 PLN.
        
        RAZEM:
        Netto: 1000.00 PLN
        VAT (8%): 100.00 PLN  <-- BŁĄD! 8% z 1000 to 80zł, nie 100zł!
        Brutto: 1100.00 PLN
        """)
    return ["demo_docs/faktura_ok.txt", "demo_docs/faktura_error.txt"]

def run_audit_demo():
    print("\n--- SCENARIUSZ 1: AUDYT FAKTUR (STRAŻNIK FINANSÓW) ---")
    print("Symulacja: Wrzucam faktury do systemu...")
    files = create_mock_invoices()
    time.sleep(1)
    
    agent = SecureAuditAgent()
    print("Agent: Analizuję dokumenty pod kątem błędów rachunkowych i formalnych...")
    
    # Uruchomienie agenta
    result = agent.process_audit("Sprawdź poprawność matematyczną faktur", files)
    
    print("\n--- WYNIK AUDYTU ---")
    if result['status'] == 'success':
        print(result['report'])
        # Jeśli jest JSON z danymi, można go ładnie wyświetlić
    else:
        print(f"Błąd audytu: {result.get('message')}")
    
    input("\n[Naciśnij ENTER, aby wrócić do menu]")

def run_chat_demo():
    print("\n--- SCENARIUSZ 2: ASYSTENT KOSZTORYSANTA (WYCENY) ---")
    print("Wpisz zapytanie o wycenę (np. 'Ile kosztuje ocieplenie 150m2 elewacji?')")
    print("lub wpisz 'demo' aby użyć gotowego przykladu.")
    
    query = input("\nTwój Kosztorys > ")
    if query.lower().strip() == 'demo':
        query = "Mamy do ocieplenia 200m2 ściany. Styropian 15cm, klej, siatka, tynk silikonowy. Robocizna nasza. Policz materiały i robociznę (przyjmij średnie stawki rynkowe)."
        print(f"Wybrano DEMO: {query}")
        
    agent = ConstructionChatAgent()
    response = agent.chat(query)
    
    print("\n--- ODPOWIEDŹ EKSPERTA ---")
    print(response)
    
    input("\n[Naciśnij ENTER, aby wrócić do menu]")

def main():
    while True:
        clear_screen()
        print("========================================")
        print("   SYNAPSA BUDOWLANKA - DEMO 2026       ")
        print("========================================")
        print("1. Audyt Faktur (Sprawdź błędy)")
        print("2. Szybka Wycena (Czat z Ekspertem)")
        print("3. Wyjście")
        
        choice = input("\nWybierz opcję (1-3): ")
        
        if choice == '1':
            run_audit_demo()
        elif choice == '2':
            run_chat_demo()
        elif choice == '3':
            print("Do widzenia!")
            break
        else:
            print("Niepoprawny wybór.")

if __name__ == "__main__":
    main()
