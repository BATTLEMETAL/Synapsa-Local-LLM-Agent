# Poradnik instalacji Synapsa na komputerze księgowej

**Dla Pana** — jak to zainstalować, nawet bez wiedzy technicznej.

---

## Wymagania komputera

Program działa na **KAŻDYM** komputerze z Windows:
- Windows 10 lub Windows 11
- Minimum 2 GB RAM (nawet stary laptop)
- **Nie potrzebuje mocnej karty graficznej**
- **Nie potrzebuje stałego internetu** (tylko przy pierwszej instalacji)

---

## Co wysłać / zanieść do księgowej

Wyślij jej cały folder `Synapsa` (np. przez pendrive lub e-mail jako ZIP).

W folderze są już gotowe pliki:
- `INSTALACJA.bat` — uruchamia się raz przy pierwszej instalacji
- `START_KSIEGOWOSC.bat` — uruchamia program codziennie
- `instrukcja_synapsa.md` — instrukcja obsługi dla księgowej

---

## Kroki instalacji (jednorazowe)

### Krok 1 — Zainstalować Python

> ⚠️ **Jeśli Python jest już zainstalowany — pominąć ten krok.**

1. Otworzyć stronę: **https://www.python.org/downloads/**
2. Kliknąć żółty przycisk **"Download Python"**
3. Uruchomić pobrany plik instalatora
4. Na **PIERWSZYM EKRANIE** zaznaczyć pole: ☑️ **"Add Python to PATH"**
5. Kliknąć **"Install Now"**
6. Poczekać na zakończenie instalacji

### Krok 2 — Uruchomić instalator Synapsa

1. Otworzyć folder `Synapsa`
2. Kliknąć **dwukrotnie** na plik `INSTALACJA.bat`
3. Poczekać — program pobierze potrzebne biblioteki (~5 min)
4. Na końcu zapyta czy uruchomić program — wpisać **T** i Enter

**Na pulpicie pojawi się skrót "Synapsa Audyt Faktur"** — od teraz wystarczy go klikać.

---

## Codzienne użytkowanie

Dwukrotne kliknięcie na **"Synapsa Audyt Faktur"** na Pulpicie.

Otworzy się przeglądarka z programem.

> 💡 **Uwaga:** Małe czarne okienko (terminal) otwiera się razem z programem — **nie zamykać go!** Można je zminimalizować.

---

## Jak przenosić faktury ze skanera?

1. Scanner zapisuje skan domyślnie w: **Dokumenty → Zeskanowane**  
   (lub na Pulpicie — zależy od ustawień skanera)
2. W programie kliknąć **"Browse files"** i wskazać ten plik
3. Gotowe!

**Tip:** Można też skonfigurować skaner żeby "skanował do Pulpitu" — wtedy plik jest zawsze w tym samym miejscu.

---

## Czy dane są bezpieczne?

Tak — program działa **wyłącznie lokalnie**. Żadne faktury, żadne numery NIP klientów nie są wysyłane do internetu. Po instalacji program działa nawet bez Wi-Fi.

---

## Problemy?

| Problem | Rozwiązanie |
|---|---|
| Program się nie odpala | Uruchom ponownie `START_KSIEGOWOSC.bat` |
| Przeglądarka się nie otworzyła | Wpisz ręcznie w przeglądarce: http://localhost:8502 |
| "Python nie znaleziony" | Zainstaluj Python od nowa, zaznaczając "Add to PATH" |
| Skan się nie odczytuje | Upewnij się że plik to JPG, PNG lub PDF |
