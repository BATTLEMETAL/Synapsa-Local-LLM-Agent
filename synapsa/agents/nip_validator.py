"""
Synapsa — NIP Validator
Walidacja polskiego numeru NIP zgodnie z algorytmem sumy kontrolnej.

Użycie:
    from synapsa.agents.nip_validator import validate_nip, extract_nip, format_nip

    ok, msg = validate_nip("123-456-32-18")  # True, "NIP poprawny"
    ok, msg = validate_nip("1234567890")     # False jeśli suma kontrolna zła

    nip = extract_nip("Firma X, NIP: 123-456-32-18, adres...")
    clean = format_nip("1234563218")  # "123-456-32-18"
"""
import re
from typing import Optional, Tuple


# Wagi dla sumy kontrolnej NIP
_NIP_WEIGHTS = [6, 5, 7, 2, 3, 4, 5, 6, 7]


def _clean_nip(raw: str) -> str:
    """Usuwa myślniki, spacje i inne separatory — zostają tylko cyfry."""
    return re.sub(r"[^0-9]", "", raw)


def validate_nip(nip_raw: str) -> Tuple[bool, str]:
    """
    Waliduje numer NIP.

    Args:
        nip_raw: NIP w dowolnym formacie (np. "123-456-32-18", "1234563218")

    Returns:
        (True, "NIP poprawny") lub (False, "komunikat błędu")
    """
    if not nip_raw or not nip_raw.strip():
        return False, "NIP jest wymagany"

    digits = _clean_nip(nip_raw)

    if len(digits) != 10:
        return False, f"NIP musi mieć 10 cyfr (podano {len(digits)})"

    if not digits.isdigit():
        return False, "NIP może zawierać tylko cyfry"

    # Suma kontrolna
    total = sum(int(digits[i]) * _NIP_WEIGHTS[i] for i in range(9))
    checksum = total % 11

    if checksum == 10:
        return False, f"NIP {format_nip(digits)} — nieprawidłowa cyfra kontrolna (suma daje 10)"

    if checksum != int(digits[9]):
        return (
            False,
            f"NIP {format_nip(digits)} — nieprawidłowa cyfra kontrolna "
            f"(oczekiwano {checksum}, podano {digits[9]})",
        )

    return True, f"NIP {format_nip(digits)} ✓"


def extract_nip(text: str) -> Optional[str]:
    """
    Wyciąga NIP z tekstu (np. z pola 'Sprzedawca').
    Zwraca czysty 10-cyfrowy string lub None.
    """
    patterns = [
        r"NIP\s*:?\s*([\d]{3}[-\s]?[\d]{3}[-\s]?[\d]{2}[-\s]?[\d]{2})",
        r"NIP\s*:?\s*([\d]{10})",
        r"\b([\d]{3}-[\d]{3}-[\d]{2}-[\d]{2})\b",
        r"\b([\d]{10})\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = _clean_nip(m.group(1))
            if len(candidate) == 10:
                return candidate
    return None


def format_nip(digits: str) -> str:
    """Formatuje 10-cyfrowy NIP jako XXX-XXX-XX-XX."""
    d = _clean_nip(digits)
    if len(d) == 10:
        return f"{d[0:3]}-{d[3:6]}-{d[6:8]}-{d[8:10]}"
    return digits


def validate_nip_from_field(field_text: str) -> Tuple[bool, str, Optional[str]]:
    """
    Waliduje NIP wyciągnięty z pola tekstowego (np. "Firma X NIP: 123-456-32-18").

    Returns:
        (is_valid, message, extracted_nip_or_None)
    """
    nip = extract_nip(field_text)
    if nip is None:
        # Brak NIP w polu — opcjonalne ostrzeżenie (nie błąd krytyczny)
        return True, "Brak NIP w polu — uzupełnij dla faktury VAT", None

    is_valid, msg = validate_nip(nip)
    return is_valid, msg, nip
