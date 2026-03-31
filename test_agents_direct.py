import os
import sys

# Setup paths
root = os.path.abspath(os.path.dirname(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

from synapsa.agents.office_agent import SecureAuditAgent
from synapsa.agents.accountant_agent import AccountantAgent

def test_audit():
    print("\n--- TEST: AUDYT FAKTUR ---")
    image_path = r"C:\Users\mz100\PycharmProjects\Synapsa\dystrybucjaoffice\SynapsaOffice\Zrzut ekranu 2026-02-16 o 12.19.09.jpeg"
    agent = SecureAuditAgent()
    instruction = "Sprawdź poprawność matematyczną faktury. Wyszukaj NIP nabywcy: 8842665572 i sprawdź czy kwoty netto + vat zgadzają się z brutto."
    
    result = agent.process_audit(instruction, [image_path])
    print("Status:", result.get('status'))
    print("Raport:\n", result.get('report'))

def test_accountant():
    print("\n--- TEST: WIRTUALNA KSIĘGOWA ---")
    agent = AccountantAgent()
    data = (
        "Wystaw fakturę wzorując się na następujących danych:\n"
        "Sprzedawca: JK ELECTRONICS Jacek Kika, NIP 8291354562\n"
        "Nabywca: STYLIZACJA RZĘS I PAZNOKCI Sandra Giemza, NIP 8842665572\n"
        "Data wystawienia: 2026-02-05\n"
        "Pozycje:\n"
        "1. JURMERRY organizer (1 szt), 161.79 PLN netto\n"
        "2. koszt przesyłki (1 szt), 16.25 PLN netto\n"
    )
    res = agent.generate_invoice(data)
    print("Wygenerowana faktura:\n", res)

if __name__ == "__main__":
    test_audit()
    test_accountant()
