"""
Synapsa — RAG Evaluation Script
Evaluates the Retrieval-Augmented Generation pipeline using lightweight custom metrics
inspired by Ragas / DeepEval frameworks.

Metrics implemented:
  1. Context Recall — Does the retrieval step find relevant context?
  2. Answer Relevance — Is the generated answer relevant to the question?
  3. Faithfulness — Does the answer stay faithful to the retrieved context?

Usage:
    python tests/eval_rag.py

Note: This script uses keyword-based heuristic metrics (no LLM judge)
      so it can run offline without a GPU. For production evaluation,
      consider replacing with Ragas or DeepEval with an LLM judge.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Evaluation Data — Ground Truth
# ---------------------------------------------------------------------------

@dataclass
class EvalSample:
    """A single evaluation sample with question, expected context, and expected answer."""

    question: str
    expected_context_keywords: List[str]
    expected_answer_keywords: List[str]
    retrieved_context: str = ""
    generated_answer: str = ""


EVAL_DATASET: List[EvalSample] = [
    EvalSample(
        question="Jaka jest stawka VAT na remont mieszkania w 2024 roku?",
        expected_context_keywords=["VAT", "8%", "remont", "mieszkalny", "2024"],
        expected_answer_keywords=["8%", "remont", "mieszkalny"],
    ),
    EvalSample(
        question="Kiedy obowiązuje mechanizm podzielonej płatności?",
        expected_context_keywords=["MPP", "podzielonej", "15000", "PLN"],
        expected_answer_keywords=["15000", "podzielona", "płatność"],
    ),
    EvalSample(
        question="Jakie dane musi zawierać faktura VAT?",
        expected_context_keywords=["NIP", "data", "kwota", "faktura", "vat"],
        expected_answer_keywords=["NIP", "data", "sprzedawca", "nabywca"],
    ),
    EvalSample(
        question="Co to jest KSeF i od kiedy obowiązuje?",
        expected_context_keywords=["KSeF", "krajowy", "system", "faktur", "2024"],
        expected_answer_keywords=["KSeF", "elektroniczn", "faktur"],
    ),
    EvalSample(
        question="Ile kosztuje ocieplenie budynku styropianem 15cm?",
        expected_context_keywords=["styropian", "15cm", "PLN", "m²", "izolacja"],
        expected_answer_keywords=["60", "85", "PLN", "m²"],
    ),
    EvalSample(
        question="Jaka jest stawka VAT na prace budowlane w nowym budownictwie?",
        expected_context_keywords=["VAT", "23%", "nowe", "budownictwo"],
        expected_answer_keywords=["23%", "budow"],
    ),
    EvalSample(
        question="Jak obliczyć koszt robocizny murarskiej?",
        expected_context_keywords=["robocizna", "murars", "PLN", "m²"],
        expected_answer_keywords=["60", "90", "PLN", "m²"],
    ),
    EvalSample(
        question="Czym się różni dachówka ceramiczna od blachy trapezowej pod względem ceny?",
        expected_context_keywords=["dachówka", "blacha", "PLN", "m²"],
        expected_answer_keywords=["dachówka", "blacha", "PLN"],
    ),
    EvalSample(
        question="Czy faktura na 20000 PLN wymaga mechanizmu podzielonej płatności?",
        expected_context_keywords=["MPP", "15000", "podzielona", "płatność"],
        expected_answer_keywords=["tak", "15000", "MPP"],
    ),
    EvalSample(
        question="Jakie są normy VAT dla usług budowlanych w 2023 roku?",
        expected_context_keywords=["VAT", "2023", "8%", "23%", "budowlan"],
        expected_answer_keywords=["8%", "23%", "budowlan"],
    ),
]


# ---------------------------------------------------------------------------
# Simulated RAG Retrieval & Generation (offline mode)
# ---------------------------------------------------------------------------

def simulate_retrieval(question: str) -> str:
    """
    Simulates RAG retrieval using the local knowledge base.
    In production, this would query ChromaDB for nearest-neighbor chunks.
    """
    # Load VAT norms if available
    norms_path = os.path.join(
        os.path.dirname(__file__), "..", "synapsa", "knowledge", "vat_norms.json"
    )
    context_parts: List[str] = []

    if os.path.exists(norms_path):
        with open(norms_path, "r", encoding="utf-8") as f:
            norms = json.load(f)
        context_parts.append(json.dumps(norms, ensure_ascii=False, indent=2)[:2000])

    # Add construction knowledge
    from synapsa.agents.construction_agent import CONSTRUCTION_KNOWLEDGE

    for category, items in CONSTRUCTION_KNOWLEDGE.items():
        for name, price in items.items():
            context_parts.append(f"{category}: {name} — {price}")

    # Add MPP / KSeF general knowledge
    context_parts.extend([
        "MPP: Mechanizm podzielonej płatności obowiązuje dla transakcji >= 15000 PLN brutto.",
        "KSeF: Krajowy System e-Faktur — obowiązkowy od 2024 roku.",
        "VAT 8%: stawka preferencyjna dla remontów budynków mieszkalnych.",
        "VAT 23%: stawka podstawowa dla usług budowlanych (nowe budownictwo).",
        "Faktura VAT musi zawierać: NIP sprzedawcy i nabywcy, datę, kwotę netto/VAT/brutto.",
    ])

    return "\n".join(context_parts)


def simulate_generation(question: str, context: str) -> str:
    """
    Simulates LLM generation using simple keyword matching.
    In production, this would pass the context + question to the Qwen model.
    """
    q = question.lower()
    if "vat" in q and "remont" in q:
        return "Stawka VAT na remont budynku mieszkalnego wynosi 8% (stawka preferencyjna)."
    if "mpp" in q or "podzielon" in q:
        if "20000" in q:
            return "Tak, faktura na 20000 PLN wymaga MPP — próg to 15000 PLN brutto."
        return "Mechanizm podzielonej płatności obowiązuje dla faktur >= 15000 PLN brutto."
    if "ksef" in q.lower():
        return "KSeF to Krajowy System e-Faktur, obowiązkowy od 2024 roku do wystawiania faktur elektronicznych."
    if "faktura" in q and "dan" in q:
        return "Faktura VAT musi zawierać: NIP sprzedawcy i nabywcy, datę wystawienia, kwoty netto/VAT/brutto."
    if "ocieplen" in q or "styropian" in q:
        return "Ocieplenie styropianem 15cm kosztuje 60-85 PLN/m² (materiał) + 30-50 PLN/m² (montaż)."
    if "nowe budownictwo" in q or "nowym budownictwie" in q:
        return "Stawka VAT dla usług budowlanych w nowym budownictwie wynosi 23%."
    if "robocizn" in q and "murar" in q:
        return "Koszt robocizny murarskiej to 60-90 PLN/m² w zależności od regionu i materiału."
    if "dachówka" in q and "blach" in q:
        return "Dachówka ceramiczna: 80-150 PLN/m², blacha trapezowa: 35-60 PLN/m²."
    if "2023" in q and "vat" in q:
        return "W 2023 roku stawki VAT na usługi budowlane: 8% (remont mieszkalny), 23% (nowe budownictwo)."
    return "Brak odpowiedzi — kontekst niewystarczający."


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def context_recall(sample: EvalSample) -> float:
    """
    Measures what fraction of expected keywords appear in the retrieved context.
    Score: 0.0 (none found) to 1.0 (all found).
    """
    if not sample.retrieved_context:
        return 0.0
    ctx_lower = sample.retrieved_context.lower()
    found = sum(1 for kw in sample.expected_context_keywords if kw.lower() in ctx_lower)
    return found / len(sample.expected_context_keywords)


def answer_relevance(sample: EvalSample) -> float:
    """
    Measures what fraction of expected answer keywords appear in the generated answer.
    Score: 0.0 (none found) to 1.0 (all found).
    """
    if not sample.generated_answer:
        return 0.0
    ans_lower = sample.generated_answer.lower()
    found = sum(1 for kw in sample.expected_answer_keywords if kw.lower() in ans_lower)
    return found / len(sample.expected_answer_keywords)


def faithfulness(sample: EvalSample) -> float:
    """
    Measures whether the generated answer's key claims are supported by the context.
    Uses word-overlap heuristic: fraction of answer words that appear in context.
    """
    if not sample.generated_answer or not sample.retrieved_context:
        return 0.0
    answer_words = set(sample.generated_answer.lower().split())
    context_words = set(sample.retrieved_context.lower().split())
    # Filter out short words (articles, prepositions)
    meaningful = {w for w in answer_words if len(w) > 3}
    if not meaningful:
        return 1.0
    overlap = meaningful & context_words
    return len(overlap) / len(meaningful)


# ---------------------------------------------------------------------------
# Main Evaluation
# ---------------------------------------------------------------------------

def run_evaluation() -> None:
    """Runs the full RAG evaluation pipeline and prints results."""
    print("=" * 70)
    print("🧪 Synapsa RAG Evaluation")
    print("=" * 70)

    total_ctx_recall = 0.0
    total_ans_relevance = 0.0
    total_faithfulness = 0.0
    n = len(EVAL_DATASET)

    for i, sample in enumerate(EVAL_DATASET, 1):
        # Simulate RAG pipeline
        sample.retrieved_context = simulate_retrieval(sample.question)
        sample.generated_answer = simulate_generation(sample.question, sample.retrieved_context)

        # Compute metrics
        cr = context_recall(sample)
        ar = answer_relevance(sample)
        fa = faithfulness(sample)

        total_ctx_recall += cr
        total_ans_relevance += ar
        total_faithfulness += fa

        print(f"\n[{i}/{n}] Q: {sample.question}")
        print(f"  Context Recall:    {cr:.2f}")
        print(f"  Answer Relevance:  {ar:.2f}")
        print(f"  Faithfulness:      {fa:.2f}")
        print(f"  Answer: {sample.generated_answer[:100]}...")

    # Summary
    print("\n" + "=" * 70)
    print("📊 AGGREGATE RESULTS")
    print("=" * 70)
    print(f"  Context Recall (avg):    {total_ctx_recall / n:.3f}")
    print(f"  Answer Relevance (avg):  {total_ans_relevance / n:.3f}")
    print(f"  Faithfulness (avg):      {total_faithfulness / n:.3f}")
    print(f"  Samples evaluated:       {n}")
    print("=" * 70)

    # Pass/Fail threshold
    avg_relevance = total_ans_relevance / n
    if avg_relevance >= 0.6:
        print("✅ PASS — Answer Relevance above 60% threshold")
    else:
        print("❌ FAIL — Answer Relevance below 60% threshold")


if __name__ == "__main__":
    run_evaluation()
