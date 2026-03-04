"""
Synapsa — ConstructionChatAgent (Asystent Budowlany)
Wzorowany na wzorcach z Obserwator.py i Audytor.py.
Specjalizuje się w kosztorysowaniu i doradztwie budowlanym.
"""
import logging

logger = logging.getLogger(__name__)


# Baza wiedzy budowlanej (offline fallback)
CONSTRUCTION_KNOWLEDGE = {
    "izolacja": {
        "styropian 10cm": "45-65 PLN/m² (materiał) + 30-50 PLN/m² (montaż)",
        "styropian 15cm": "60-85 PLN/m² (materiał) + 30-50 PLN/m² (montaż)",
        "wełna mineralna": "55-90 PLN/m² (materiał) + 35-55 PLN/m² (montaż)",
        "ocieplenie dachu": "80-140 PLN/m² kompleksowo",
    },
    "mury": {
        "beton komórkowy": "280-350 PLN/m³ (bloczek) + 60-90 PLN/m² (robocizna)",
        "cegła ceramiczna": "350-500 PLN/m³ (materiał) + 80-120 PLN/m² (robocizna)",
        "pustak": "220-300 PLN/m³ (materiał) + 60-90 PLN/m² (robocizna)",
    },
    "pokrycie_dachu": {
        "dachówka ceramiczna": "80-150 PLN/m²",
        "blacha trapezowa": "35-60 PLN/m²",
        "papa termozgrzewalna": "40-70 PLN/m²",
        "gonty bitumiczne": "45-75 PLN/m²",
    },
    "tynki": {
        "tynk maszynowy wewnętrzny": "25-45 PLN/m²",
        "tynk elewacyjny": "40-75 PLN/m²",
        "gładź gipsowa": "20-35 PLN/m²",
    },
    "podłogi": {
        "wylewka betonowa": "30-55 PLN/m²",
        "panele laminowane": "40-80 PLN/m² (materiał+montaż)",
        "płytki ceramiczne": "60-120 PLN/m² (materiał+montaż)",
        "deska drewniana": "80-180 PLN/m² (materiał+montaż)",
    },
    "instalacje": {
        "instalacja elektryczna (dom 150m2)": "15000-30000 PLN",
        "instalacja wod-kan (dom 150m2)": "12000-25000 PLN",
        "centralne ogrzewanie CO": "20000-45000 PLN",
        "pompa ciepła": "35000-70000 PLN",
        "fotowoltaika 10kW": "35000-55000 PLN",
    },
}


class ConstructionChatAgent:
    """Asystent budowlany do kosztorysowania i porad."""

    def __init__(self, engine=None):
        if engine is None:
            try:
                from synapsa.engine import SynapsaEngine
                self.engine = SynapsaEngine.get_instance()
            except Exception:
                self.engine = None
        else:
            self.engine = engine

    def _format_knowledge_context(self) -> str:
        """Formatuje bazę wiedzy budowlanej dla promptu AI."""
        lines = []
        for category, items in CONSTRUCTION_KNOWLEDGE.items():
            lines.append(f"\n{category.upper().replace('_', ' ')}:")
            for name, price in items.items():
                lines.append(f"  • {name}: {price}")
        return "\n".join(lines)

    def chat(self, user_message: str) -> str:
        """
        Odpowiada na pytanie budowlane.
        Strategia: 1) Szukaj w lokalnej bazie wiedzy (natychmiastowa, konkretna odpowiedź)
                   2) Jeśli pytanie jest ogólne — użyj AI engine
        """
        # KROK 1: Sprawdź bazę wiedzy dla konkretnego materiału/usługi
        offline_match = self._offline_answer(user_message)
        if "📊 **Szacunkowe koszty**" in offline_match:
            # Mamy konkretną odpowiedź z cenami — zwróć ją!
            # Opcjonalnie wzbogac przez AI jeśli dostępne
            if self.engine and self.engine.model:
                # Mamy prawdziwy model — daj mu bazowe ceny + kontekst
                prompt = f"""Jesteś Asystentem Budowlanym AI.

BAZA CENOWA (FAKTY — nie zmieniaj tych liczb!):
{offline_match}

PYTANIE KLIENTA: {user_message}

Na podstawie powyższych AKTUALNYCH CEN odpowiedz konkretnie.
Podaj szacunek całkowity dla podanego metrażu jeśli został podany.
Uwzględnij materiał + robocizna + krótkie wskazówki."""
                return self.engine._generate_with_model(prompt, max_tokens=600)
            else:
                # Offline — wzbogać odpowiedź o kalkulację metrażową
                return self._enrich_with_calculation(user_message, offline_match)

        # KROK 2: Pytanie ogólne — użyj engine (z pełną bazą w kontekście)
        if self.engine:
            knowledge_ctx = self._format_knowledge_context()
            prompt = f"""Jesteś Asystentem Budowlanym AI ("Synapsa Budowlanka").
Specjalizujesz się w kosztorysowaniu prac budowlanych w Polsce.

BAZA CENOWA (aktualne ceny rynkowe 2026):
{knowledge_ctx}

PYTANIE KLIENTA:
{user_message}

ZASADY ODPOWIEDZI:
1. Podaj szacunkowe koszty (jeśli pytanie dotyczy cen)
2. Uwzględnij materiały + robociznę osobno
3. Wskaż czynniki wpływające na cenę (region, gatunek, itp.)
4. Bądź konkretny i pomocny
5. Odpowiedz po polsku

ODPOWIEDŹ:"""
            return self.engine.generate(prompt, max_tokens=800)
        else:
            return offline_match

    def _enrich_with_calculation(self, question: str, base_answer: str) -> str:
        """Wyciąga metraz z pytania i oblicza szacunek całkowity."""
        import re
        metr_match = re.search(r'(\d+)\s*m[²2]', question)
        if metr_match:
            m2 = int(metr_match.group(1))
            # Wyciągamy zakres cen z odpowiedzi
            price_match = re.search(r'(\d+)-(\d+)\s*PLN/m²', base_answer)
            if price_match:
                low = int(price_match.group(1)) * m2
                high = int(price_match.group(2)) * m2
                calc = (f"\n\n💰 **Kalkulacja dla {m2} m²:**\n"
                        f"  • Minimalne: **{low:,} PLN**\n"
                        f"  • Maksymalne: **{high:,} PLN**\n"
                        f"  • Średnie: **{(low+high)//2:,} PLN**\n"
                        f"\n*Ostateczna cena zależy od regionu, dostępności ekip i konkretnego materiału.*")
                return base_answer + calc
        return base_answer

    def _offline_answer(self, question: str) -> str:
        """Odpowiedź offline z lokalnej bazy wiedzy."""
        q = question.lower()
        results = []

        # Szukanie w lokalnej bazie
        for category, items in CONSTRUCTION_KNOWLEDGE.items():
            for item_name, price in items.items():
                if any(word in q for word in item_name.lower().split()):
                    results.append(f"• **{item_name}**: {price}")

        if results:
            return (
                f"📊 **Szacunkowe koszty** (ceny rynkowe 2026, Polska):\n\n"
                + "\n".join(results)
                + "\n\n*Ceny mogą się różnić zależnie od regionu, dostawcy i zakresu prac.*"
            )

        # Generic answer
        return (
            "🏗️ **Asystent Budowlany**\n\n"
            "Mogę pomóc z wyceną:\n"
            "• Izolacji termicznej i elewacji\n"
            "• Pokrycia dachu\n"
            "• Tynków i podłóg\n"
            "• Instalacji (elektrycznej, wod-kan, ogrzewania)\n"
            "• Murowania i konstrukcji\n\n"
            f"Zapytaj konkretnie np.: *'Ile kosztuje ocieplenie 200m2 styropianem 15cm?'*"
        )
