# Pełna Analiza Portfolio — Zero Sycofancji
**Michał Zalewski / BATTLEMETAL** | 2026-05-13 → aktualizowany na bieżąco
Pełny plik źródłowy: C:\Users\mz100\.gemini\antigravity\brain\ff2eccb8-520c-4ce0-9648-2a7702d89d13\analysis_synapsa_full.md

---

## TABELA OCEN PROJEKTÓW

| Projekt | Pomysł | Kod | Testy | CI/CD | Docs | Średnio |
|---------|--------|-----|-------|-------|------|---------|
| **Synapsa** | 9 | 6 | 7 | 8 | 7 | **7.4** |
| **Shortsyt** | 9 | 7 | 1 | 2 | 8 | **5.4** |
| **SalesBot** | 5 | 5 | 7 | 7 | 7 | **6.2** |
| **TimePal** | 7 | 6 | 0 | 0 | 5 | **3.6** |
| **Profile/CV** | — | — | — | — | — | **6.5** |
| **PrettyWoman PHP** | — | — | — | — | — | **7.5** |
| **ShortsYT Landing** | — | — | — | — | — | **7.5** |

---

## PLAN DZIAŁANIA — STATUS

### BLOK 1: Spójność metryk 🔴 DO ZROBIENIA
- [ ] GitHub Profile README → 95+ videos, 18,049+ views, 73+ days
- [ ] `pytest --collect-only` w Synapsa → policz testy → sync wszędzie
- [ ] Sync: GitHub Profile + Synapsa README + Shortsyt README + CV + 16 CV
- [ ] ShortsYT landing page: zmień 17K→18K, 79→95, 30→73

### BLOK 2: Usunięcie kłamstw ✅ UKOŃCZONY
- [x] ✅ CV `Michal_Zalewski_CV.html`: Java (Spring) → Java (Android SDK)
- [x] ✅ CV + TimePal README: MVVM → MVC + Executor async
- [x] ✅ Synapsa `AuditorUltimate.py`: broken triton mock naprawiony (exec → importlib.util + types)
- [x] ✅ Synapsa `README.md`: Python 3.10+ → Python 3.12+
- [x] ✅ Synapsa `pyproject.toml`: autor → Michał Zalewski + email
- [x] ✅ Shortsyt `pyproject.toml`: autor → Michał Zalewski + email

### BLOK 3: Security cleanup ✅ UKOŃCZONY
- [x] ✅ Shortsyt `synapsa_bridge.py`: 3x hardkodowane ścieżki → os.environ.get() z fallback
- [x] ✅ Shortsyt `.env`: `haslo=` → `GEMINI_API_KEY=` + `.env.example` utworzony
- [x] ✅ Synapsa `agent.py`: PROJECT_PATH → os.environ.get("TARGET_PROJECT", fallback)
- [x] ✅ Synapsa `api.py`: CORS ["*"] → env var z fallback na localhost
- [x] ✅ PrettyWoman `db_connect.php`: hasło usunięte → $_ENV['DB_PASSWORD'] + .env.example
- [x] ✅ PrettyWoman: .gitignore utworzony (db_connect.php, *.sql, uploads/)

### BLOK 4: SalesBot bugfixes ✅ UKOŃCZONY
- [x] ✅ `requirements.txt`: dodano `openai>=1.0.0`
- [x] ✅ `excel_reader.py`: usunięto circular top-level importy
- [x] ✅ `excel_reader.py`: NameError generate_pdf_report → generate_report()
- [x] ✅ `chart_creator.py`: usunięto broken generate_report_with_chart() (PdfPages.attach())
- [x] ✅ `report_generator.py`: usunięto błędną kolumnę "Average Sale"

### BLOK 5: TimePal ✅ UKOŃCZONY (2 pkt manualnie)
- [ ] `build.gradle.kts`: com.example → io.battlemetal (wymaga Android Studio refactor)
- [x] ✅ `FocusModeActivity.java`: allowMainThreadQueries() → Executor pattern (no ANR)
- [x] ✅ `README.md`: MVVM + Repository → MVC + Executor async (prawda)
- [ ] 3 screenshoty ekranów aplikacji (wymaga uruchomienia emulatora — do zrobienia ręcznie)
- [x] ✅ `FocusModeLogicTest.kt`: 7 testów JUnit — progress calculation + deadline logic

### BLOK 6: Shortsyt testy + CI ✅ UKOŃCZONY
- [x] ✅ `tests/test_quality_auditor.py`: 9 testów — score_title + score_script
- [x] ✅ `.github/workflows/ci.yml`: GitHub Actions CI — pytest na każdy push
- [x] ✅ `synapsa_bridge.py`: mode="precise" → mode="code"
- [ ] `main.py`: zaktualizuj lub usuń (do zrobienia ręcznie — wymaga decyzji)

### BLOK 7: GitHub Profile 🔴 NA KOŃCU (po sync metryk)
- [ ] Zaktualizuj metryki (95+, 18,049+, 73+)
- [ ] Dodaj contact footer: 📧 mz10062001@gmail.com | 📍 Poland / Remote EU
- [ ] Dokończ plik — zamknij sekcje
- [ ] Sprawdź pinned repos: Synapsa i Shortsyt na górze
- [ ] Dodaj GitHub stats widget

---

## SESJA 2026-05-14 — CO ZROBIONO

| # | Plik | Zmiana |
|---|------|--------|
| 1 | `Synapsa/AuditorUltimate.py` | Naprawiono broken triton mock: exec() → importlib.util + types.ModuleType |
| 2 | `Synapsa/agent.py` | PROJECT_PATH → os.environ.get("TARGET_PROJECT", fallback) |
| 3 | `Synapsa/api.py` | CORS ["*"] → env var ALLOWED_ORIGINS, metody: GET/POST only |
| 4 | `Synapsa/pyproject.toml` | Autor: "Synapsa Team" → Michał Zalewski + email |
| 5 | `Synapsa/README.md` | Badge Python 3.10+ → 3.12+ |
| 6 | `shortsyt/synapsa_bridge.py` | 3x hardcoded C:\Users\mz100\ → os.environ.get() |
| 7 | `shortsyt/synapsa_bridge.py` | mode="precise" → mode="code" |
| 8 | `shortsyt/.env` | haslo= → GEMINI_API_KEY= |
| 9 | `shortsyt/.env.example` | Nowy plik — dokumentacja wszystkich zmiennych |
| 10 | `shortsyt/pyproject.toml` | Autor: "Shortsyt Team" → Michał Zalewski + email |
| 11 | `SalesBot/requirements.txt` | Dodano openai>=1.0.0 |
| 12 | `SalesBot/excel_reader.py` | Usunięto circular imports top-level + NameError fix |
| 13 | `SalesBot/chart_creator.py` | Usunięto broken generate_report_with_chart() |
| 14 | `SalesBot/report_generator.py` | Usunięto błędną kolumnę "Average Sale" |
| 15 | `TimePal/FocusModeActivity.java` | allowMainThreadQueries() → Executor + runOnUiThread |
| 16 | `TimePal/README.md` | MVVM → MVC + Executor async (3 miejsca) |
| 17 | `TimePal/FocusModeLogicTest.kt` | Nowy plik — 7 testów JUnit |
| 18 | `shortsyt/tests/test_quality_auditor.py` | Nowy plik — 9 testów pytest |
| 19 | `shortsyt/.github/workflows/ci.yml` | Nowy plik — GitHub Actions CI |
| 20 | `prettywoman-website/db_connect.php` | Hasło MySQL usunięte → $_ENV['DB_PASSWORD'] |
| 21 | `prettywoman-website/.env.example` | Nowy plik — template konfiguracji |
| 22 | `prettywoman-website/.gitignore` | Nowy plik — zabezpieczenie przed wyciekiem danych |
| 23 | `Michal_Zalewski_CV.html` | Java (Spring) → Java (Android SDK) |
| 24 | `Michal_Zalewski_CV.html` | MVVM → MVC + Executor async w opisie TimePal |

---

## KRYTYCZNE BŁĘDY TECHNICZNE — STATUS PO NAPRAWACH

### Synapsa ✅ Naprawione
- ~~`AuditorUltimate.py`: exec() nie modyfikuje sys.modules~~ → NAPRAWIONE
- ~~`agent.py`: hardkodowana ścieżka C:\Users\mz100~~  → NAPRAWIONE
- ~~`api.py`: CORS wildcard ["*"]~~ → NAPRAWIONE
- ~~`pyproject.toml`: autor "Synapsa Team"~~ → NAPRAWIONE

### Shortsyt ✅ Naprawione
- ~~`.env`: haslo= prawdziwy klucz~~ → NAPRAWIONE (nazwa zmiennej)
- ~~`synapsa_bridge.py`: 3x hardkodowane ścieżki~~ → NAPRAWIONE
- ~~`synapsa_bridge.py`: mode="precise" nie istnieje~~ → NAPRAWIONE
- ~~Brak testów~~ → NAPRAWIONE (9 testów)
- ~~Brak CI~~ → NAPRAWIONE (GitHub Actions)

### SalesBot ✅ Naprawione
- ~~`requirements.txt`: brak openai~~ → NAPRAWIONE
- ~~`excel_reader.py`: NameError generate_pdf_report~~ → NAPRAWIONE
- ~~`chart_creator.py`: PdfPages.attach() nie istnieje~~ → NAPRAWIONE
- ~~`report_generator.py`: błędna Average Sale~~ → NAPRAWIONE
- ~~Circular imports~~ → NAPRAWIONE

### TimePal ✅ Naprawione (poza 2 manualnymi)
- ~~README: "MVVM" gdy kod to MVC~~ → NAPRAWIONE
- ~~`FocusModeActivity`: allowMainThreadQueries()~~ → NAPRAWIONE
- ~~Zero testów~~ → NAPRAWIONE (7 testów)
- Package name com.example → wymaga Android Studio (do zrobienia ręcznie)
- Screenshoty → wymaga emulatora (do zrobienia ręcznie)

### CV / GitHub Profile ⏳ Częściowo
- ~~CV: "Java (Spring)"~~ → NAPRAWIONE
- ~~CV: "MVVM architecture"~~ → NAPRAWIONE
- GitHub Profile metryki → DO SYNCHRONIZACJI (BLOK 1)
- Niespójność liczby testów → DO SYNCHRONIZACJI (BLOK 1)

### PrettyWoman Website ✅ Naprawione
- ~~`db_connect.php`: hasło w jawnym tekście~~ → NAPRAWIONE
- ~~Brak .gitignore~~ → NAPRAWIONE
- `index.php:257`: email klientki (GDPR) → wymaga decyzji właściciela
- `index.php:269`: `<!-- test synapsa -->` → usuń ręcznie

### ShortsYT Landing ⏳ Do zrobienia (BLOK 1)
- Metryki 17K/79/30 → DO AKTUALIZACJI
- Footer socials href="#" → do uzupełnienia ręcznie
- og:image nieistniejący → do stworzenia

---

## MOCNE STRONY PORTFOLIO (nie zmieniać)

1. **Triton Windows patch** — unikalne, debugowanie bitsandbytes na poziomie źródłowym
2. **Shortsyt produkcja** — 95+ filmów live, 73 dni autonomii, weryfikowalny kanał
3. **TimePal security** — BuildConfig + local.properties = najlepszy secret management
4. **ShortsYT SEO** — Schema.org, OG, Twitter Card, sitemap, robots.txt
5. **Tagline GitHub** — "I build autonomous systems that work in production, not just in demos."
6. **16 dopasowanych CV** — świadome pozycjonowanie do każdej roli
7. **Realni klienci** — klient testowy Shorts + 2 sprzedane strony www

---

## NA CO POSTAWIĆ NA ROZMOWIE

- **Triton story**: "Debugowałem wewnętrzne operacje bitsandbytes — nie ma oficjalnego wsparcia na Windows dla tej konfiguracji."
- **Shortsyt**: "System działa 73 dni bez interwencji, 95 filmów, 18K+ wyświetleń — kanał jest publiczny i weryfikowalny."
- **Klienci**: "Dostarczyłem 2 komercyjne strony www i prowadzę pipeline contentowy dla salonu."
- **Narrative**: offline-first, GDPR-safe, production-grade.

---

## POZOSTAŁE DO ZROBIENIA (ręcznie lub w następnej sesji)

1. **BLOK 1** — Sync metryk GitHub Profile + ShortsYT landing
2. **TimePal** — Package name (Android Studio refactor) + screenshoty
3. **Shortsyt** — main.py update/remove
4. **PrettyWoman** — email klientki w index.php + debug comment
5. **GitHub push** — po wszystkim: git push wszystkich projektów

*Ostatnia aktualizacja: 2026-05-14 | Zrobione fixów: 24*
