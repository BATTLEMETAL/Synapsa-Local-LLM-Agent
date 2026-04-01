# Dokumentacja Techniczna Synapsa Professional

Ten dokument opisuje technologie i frameworki wybrane do budowy platformy Synapsa.

## 1. Języki Programowania
- **Backend**: Python 3.13+ (Główna logika, agenty AI, zarządzanie modelami).
- **Frontend**: JavaScript (ES6+), HTML5, CSS3.

## 2. Frameworki i Biblioteki

### Backend (Główny Silnik)
- **FastAPI**: Wybrany jako serce API ze względu na wysoką wydajność, natywną obsługę asynchroniczności (asyncio) i automatyczną dokumentację dokumentację Swagger.
- **Uvicorn**: Serwer ASGI zapewniający stabilne działanie API.
- **Pydantic**: Walidacja danych i zarządzanie schematami żądań/odpowiedzi.

### Local AI Stack (Silnik Modelu)
- **Transformers (Hugging Face)**: Do ładowania i obsługi modelu bazowego (Qwen 2.5 Coder).
- **PEFT (LoRA)**: Obsługa Twoich własnych "mózgów" (adapterów), które doładowują wiedzę do modelu bez konieczności przeładowywania całości.
- **BitsAndBytes**: Wykorzystany do 4-bitowej kwantyzacji (NF4), co pozwala na uruchomienie modelu 7B na kartach z 12GB VRAM (np. RTX 3060/4060).
- **Accelerate**: Optymalizacja rozmieszczenia modelu na dostępnej pamięci VRAM/RAM.

### Pamięć i Baza Danych
- **ChromaDB**: Wektorowa baza danych wykorzystana do "Pamięci Projektu". Pozwala na semantyczne przeszukiwanie kodu (AI nie tylko czyta tekst, ale rozumie znaczenie funkcji).
- **Sentence-Transformers**: Model `all-MiniLM-L6-v2` służący do zamiany kodu na wektory (embeddingi) — zapewnia kompatybilność z Twoimi oryginalnymi skryptami.

### Frontend (Interfejs Użytkownika)
- **Profesjonalny Dashboard**: Zbudowany w czystym Javascripcie (Vanilla JS) dla maksymalnej szybkości ładowania i braku zbędnych zależności.
- **Streamlit**: Wykorzystany jako pomocniczy panel diagnostyczny (`ui.py`) do monitorowania statystyk VRAM i szybkiego testowania audytów.

## 3. Architektura
System opiera się na wzorcu **Singleton** (Silnik AI), co gwarantuje, że model jest ładowany do pamięci VRAM tylko raz i współdzielony między wszystkimi agentami (Koder, Audytor, Architekt), co oszczędza zasoby i zapobiega błędom "Out of Memory".
