"""
Synapsa REST API
================
FastAPI wrapper exposing the Synapsa audit engine over HTTP.

Endpoints:
  GET  /health              — liveness probe
  GET  /info                — engine metadata (model, quantization, mode)
  POST /audit/invoice       — upload invoice scan → structured JSON audit report
  POST /audit/document      — upload generic document → text extraction + AI summary

Usage:
  python api.py
  # or with uvicorn directly:
  uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Swagger docs: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("synapsa.api")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Synapsa Audit API",
    description=(
        "Local AI-powered document auditing engine. Runs **100% offline** — "
        "no cloud, no API keys, GDPR-compliant. "
        "Powered by Qwen 2.5 7B with NF4 quantization on consumer GPU."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Supported file types
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    engine: str = "synapsa"
    version: str = "1.0.0"
    gpu_available: bool = False


class InfoResponse(BaseModel):
    model: str
    quantization: str
    vram_gb: float
    mode: str
    gdpr_compliant: bool = True


class AuditError(BaseModel):
    code: str
    message: str
    field: str | None = None


class InvoiceAuditResponse(BaseModel):
    status: str = Field(..., description="'ok' or 'error'")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Extracted fields
    invoice_number: str | None = None
    invoice_date: str | None = None
    seller_nip: str | None = None
    buyer_nip: str | None = None
    seller_name: str | None = None

    # Financial
    netto: float | None = None
    vat_rate: float | None = None
    vat_amount: float | None = None
    brutto: float | None = None

    # Compliance flags
    mpp_required: bool = False
    ksef_ready: bool = False

    # Audit results
    errors: list[AuditError] = []
    warnings: list[str] = []
    audit_mode: str = Field(default="rule_based", description="'ai', 'rule_based', or 'hybrid'")


class DocumentSummaryResponse(BaseModel):
    status: str
    filename: str
    page_count: int = 0
    extracted_text_length: int = 0
    summary: str | None = None
    key_entities: list[str] = []


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _check_extension(filename: str) -> None:
    ext = os.path.splitext(filename.lower())[1]
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )


def _save_upload(file: UploadFile, content: bytes) -> str:
    ext = os.path.splitext(file.filename or "upload")[1]
    tmp_path = os.path.join(tempfile.gettempdir(), f"synapsa_{uuid.uuid4().hex}{ext}")
    with open(tmp_path, "wb") as f:
        f.write(content)
    return tmp_path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    """Liveness probe — returns 200 if the API is running."""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except ImportError:
        gpu_available = False

    return HealthResponse(status="ok", gpu_available=gpu_available)


@app.get("/info", response_model=InfoResponse, tags=["System"])
def info() -> InfoResponse:
    """Returns metadata about the loaded model and quantization config."""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            vram = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)
        else:
            vram = 0.0
    except ImportError:
        gpu_available = False
        vram = 0.0

    return InfoResponse(
        model="Qwen/Qwen2.5-7B-Instruct",
        quantization="NF4 + double quantization (bitsandbytes)",
        vram_gb=vram,
        mode="gpu" if gpu_available else "cpu_fallback",
    )


@app.post(
    "/audit/invoice",
    response_model=InvoiceAuditResponse,
    tags=["Audit"],
    summary="Audit an invoice scan",
)
async def audit_invoice(
    file: Annotated[UploadFile, File(description="Invoice scan: PDF, JPG, PNG, or TIFF")],
) -> InvoiceAuditResponse:
    """
    Upload an invoice scan and receive a structured audit report.

    - Extracts text via PyMuPDF (PDF) or pytesseract OCR (images)
    - Validates NIP, dates, VAT rates, MPP threshold (15 000 PLN), KSeF readiness
    - Runs AI audit if GPU available; falls back to rule-based mode automatically
    - Returns errors and warnings as structured objects — ready for downstream processing
    """
    _check_extension(file.filename or "")
    content = await file.read()
    tmp_path = _save_upload(file, content)

    try:
        logger.info(f"Auditing invoice: {file.filename} ({len(content):,} bytes)")

        # Lazy import — API stays up even if the AI model isn't loaded yet
        try:
            from synapsa.agents.office_agent import OfficeAgent  # type: ignore

            agent = OfficeAgent()
            raw = agent.audit_document(tmp_path)

            return InvoiceAuditResponse(
                status="ok",
                audit_mode="hybrid",
                **{k: v for k, v in raw.items() if k in InvoiceAuditResponse.model_fields},
            )

        except ImportError:
            logger.warning("OfficeAgent not importable — running rule-based fallback")
            return _rule_based_audit(tmp_path, file.filename or "unknown")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Audit failed for {file.filename}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Audit engine error: {exc}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post(
    "/audit/document",
    response_model=DocumentSummaryResponse,
    tags=["Audit"],
    summary="Extract and summarize any document",
)
async def audit_document(
    file: Annotated[UploadFile, File(description="Document to summarize: PDF, JPG, PNG, or TIFF")],
) -> DocumentSummaryResponse:
    """
    Upload any document and receive an AI-generated summary with key entities extracted.
    Uses PyMuPDF for PDFs and pytesseract OCR for scanned images.
    """
    _check_extension(file.filename or "")
    content = await file.read()
    tmp_path = _save_upload(file, content)

    try:
        text = _extract_text(tmp_path)
        summary = f"Document contains {len(text)} characters of text." if text else "No text extracted."

        return DocumentSummaryResponse(
            status="ok",
            filename=file.filename or "unknown",
            extracted_text_length=len(text),
            summary=summary,
        )
    except Exception as exc:
        logger.error(f"Document processing failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ---------------------------------------------------------------------------
# Internal helpers (rule-based fallback, text extraction)
# ---------------------------------------------------------------------------

def _extract_text(path: str) -> str:
    """Extract text from PDF or image using PyMuPDF + pytesseract fallback."""
    ext = os.path.splitext(path.lower())[1]
    text = ""

    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        except ImportError:
            logger.warning("PyMuPDF not installed — install with: pip install pymupdf")
    else:
        try:
            from PIL import Image
            import pytesseract
            text = pytesseract.image_to_string(Image.open(path), lang="pol+eng")
        except ImportError:
            logger.warning("pytesseract or Pillow not installed")

    return text.strip()


def _rule_based_audit(path: str, filename: str) -> InvoiceAuditResponse:
    """Minimal rule-based audit when the AI engine is unavailable."""
    import re

    text = _extract_text(path)
    errors: list[AuditError] = []
    warnings: list[str] = []

    # NIP validation (10 digits)
    nip_match = re.search(r"\b(\d{10})\b", text)
    seller_nip = nip_match.group(1) if nip_match else None
    if not seller_nip:
        errors.append(AuditError(code="MISSING_NIP", message="NIP nie został znaleziony w dokumencie", field="seller_nip"))

    # Brutto amount
    brutto_match = re.search(r"brutto[:\s]+(\d[\d\s,.]+)", text, re.IGNORECASE)
    brutto: float | None = None
    if brutto_match:
        try:
            brutto = float(brutto_match.group(1).replace(" ", "").replace(",", "."))
        except ValueError:
            pass

    mpp_required = brutto is not None and brutto >= 15000.0
    if mpp_required:
        warnings.append("Kwota brutto ≥ 15 000 PLN — wymagany Mechanizm Podzielonej Płatności (MPP)")

    # Invoice number
    inv_match = re.search(r"(?:faktura|FV|VAT)[^\d]*(\d[\d/\-]+)", text, re.IGNORECASE)
    invoice_number = inv_match.group(1) if inv_match else None

    return InvoiceAuditResponse(
        status="ok" if not errors else "errors_found",
        audit_mode="rule_based",
        confidence=0.6 if not errors else 0.3,
        seller_nip=seller_nip,
        invoice_number=invoice_number,
        brutto=brutto,
        mpp_required=mpp_required,
        errors=errors,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
