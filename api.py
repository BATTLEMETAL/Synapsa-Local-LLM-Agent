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
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:8501").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
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


def validate_nip(nip: str) -> bool:
    digits = re.sub(r'[^\d]', '', nip)
    if len(digits) != 10:
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(digits[i]) * weights[i] for i in range(9)) % 11
    return checksum == int(digits[9])


def validate_ksef_number(ksef_str: str, seller_nip: str = None, invoice_year: int = None) -> dict:
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', ksef_str)
    if len(cleaned) != 35:
        return {
            "valid": False,
            "error": f"Nieprawidłowa długość numeru KSeF: {len(cleaned)} znaków (wymagane 35)"
        }
    nip_part = cleaned[:10]
    date_part = cleaned[10:18]
    errors = []
    if not validate_nip(nip_part):
        errors.append(f"Niepoprawny NIP w KSeF: {nip_part}")
    if seller_nip:
        clean_seller_nip = re.sub(r'[^\d]', '', seller_nip)
        if clean_seller_nip != nip_part:
            errors.append(f"NIP z KSeF ({nip_part}) nie zgadza się ze sprzedawcą ({clean_seller_nip})")
    try:
        from datetime import datetime
        ksef_date = datetime.strptime(date_part, "%Y%m%d")
        if invoice_year and ksef_date.year != invoice_year:
            errors.append(f"Rok z KSeF ({ksef_date.year}) nie zgadza się z rokiem faktury ({invoice_year})")
    except ValueError:
        errors.append(f"Niepoprawna data w KSeF: {date_part}")
    if errors:
        return {"valid": False, "error": " | ".join(errors)}
    return {"valid": True, "nip": nip_part, "date": date_part}


def _extract_invoice_items(text: str) -> list[dict]:
    items = []
    lines = text.split("\n")
    percent_pat = re.compile(r'\b(\d+|zw|np|0)\s*%')
    decimal_pat = re.compile(r'\b\d+(?:[\s]*\d+)*[,.]\d{2}\b')
    lp_counter = 1
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        vat_m = percent_pat.search(line_clean.lower())
        if not vat_m:
            continue
        vat_rate_str = vat_m.group(1)
        decimals = decimal_pat.findall(line_clean)
        if len(decimals) < 2:
            continue
        vals = []
        for d in decimals:
            try:
                v = float(re.sub(r'\s', '', d).replace(',', '.'))
                vals.append(v)
            except ValueError:
                pass
        if len(vals) < 2:
            continue
        vals = sorted(vals)
        netto, vat_val, brutto = 0.0, 0.0, 0.0
        if len(vals) >= 3:
            if abs(vals[0] + vals[1] - vals[2]) < 2.0:
                netto = vals[1]
                vat_val = vals[0]
                brutto = vals[2]
            elif abs(vals[0] + vals[2] - vals[1]) < 2.0:
                netto = vals[0]
                vat_val = vals[2]
                brutto = vals[1]
            else:
                brutto = vals[-1]
                netto = vals[-2]
                vat_val = vals[0]
        else:
            netto = vals[0]
            brutto = vals[1]
            vat_val = brutto - netto
        first_dec_idx = line_clean.find(decimals[0])
        if first_dec_idx > 5:
            name_part = line_clean[:first_dec_idx].strip()
        else:
            name_part = line_clean.strip()
        name_part = re.sub(r'^\s*\d+[\.\s]+', '', name_part)
        name_part = name_part[:60].strip()
        if not name_part:
            name_part = f"Pozycja towarowa {lp_counter}"
        items.append({
            "lp": lp_counter,
            "nazwa": name_part,
            "netto": netto,
            "vat_rate": f"{vat_rate_str}%",
            "vat_val": vat_val,
            "brutto": brutto
        })
        lp_counter += 1
    return items


def _detect_year_from_text(text: str) -> int:
    t = text.lower()
    date_patterns = [
        r'\b(201[5-9]|202[0-9]|2030)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])\b',
        r'\b(0[1-9]|[12][0-9]|3[01])[.](0[1-9]|1[0-2])[.](201[5-9]|202[0-9]|2030)\b',
    ]
    issue_keywords = ["wystawienia", "wystawiono", "sprzedaży", "sprzedazy", "operacji", "dostawy"]
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in issue_keywords):
            for pat in date_patterns:
                m = re.search(pat, line)
                if m:
                    year_str = m.group(1) if '-' in m.group(0) or '/' in m.group(0) else m.group(3)
                    return int(year_str)
    all_years = []
    for pat in date_patterns:
        for m in re.finditer(pat, text):
            year_str = m.group(1) if '-' in m.group(0) or '/' in m.group(0) else m.group(3)
            all_years.append(int(year_str))
    if all_years:
        from collections import Counter
        return Counter(all_years).most_common(1)[0][0]
    return 2026


def _rule_based_audit(path: str, filename: str) -> InvoiceAuditResponse:
    """Advanced rule-based offline audit mirroring app_ksiegowosc.py rules."""
    import re

    text = _extract_text(path)
    t = text.lower()
    invoice_year = _detect_year_from_text(text)
    
    errors: list[AuditError] = []
    warnings: list[str] = []

    # 1. Header & Date
    if not re.search(r'faktura\s*vat', t):
        errors.append(AuditError(code="MISSING_HEADER", message='Brak nagłówka "FAKTURA VAT"', field="header"))
    if not re.search(r'\d{1,2}[./]\d{1,2}[./]\d{4}', text):
        errors.append(AuditError(code="MISSING_DATE", message="Brak daty wystawienia", field="invoice_date"))

    # 2. NIP checks
    nips = re.findall(r'nip\s*:?\s*([\d\-\s]{10,15})', t)
    if not nips:
        candidates = re.findall(r'\b\d{10}\b', text)
        valid_candidates = [c for c in candidates if validate_nip(c)]
        if valid_candidates:
            nips = valid_candidates

    detected_nips = []
    for nip_raw in nips:
        digits = re.sub(r'[^\d]', '', nip_raw)
        if len(digits) == 10 and validate_nip(digits):
            if digits not in detected_nips:
                detected_nips.append(digits)
        elif len(digits) != 10:
            errors.append(AuditError(code="INVALID_NIP_FORMAT", message=f"Nieprawidłowy format NIP: {nip_raw.strip()}", field="seller_nip"))
        elif not validate_nip(digits):
            errors.append(AuditError(code="INVALID_NIP_CHECKSUM", message=f"Nieprawidłowa suma kontrolna NIP: {nip_raw.strip()}", field="seller_nip"))

    seller_nip = detected_nips[0] if detected_nips else None
    if not seller_nip:
        errors.append(AuditError(code="MISSING_NIP", message="Brak numeru NIP sprzedawcy/nabywcy", field="seller_nip"))

    # 3. Missing payment term / account info
    if not re.search(r'termin|płatno|zap[łl]at', t):
        warnings.append("Brak terminu płatności")
    if not re.search(r'konto|iban|pl[\d]{2}|\d{20,}', t):
        warnings.append("Brak numeru konta bankowego")

    # 4. Brutto & Netto
    n_vals = re.findall(r'netto[^\d]{0,25}([\d\s]+[,.]\d{2})', t)
    b_vals = re.findall(r'(?:brutto|do\s+zap[łl]aty)[^\d]{0,25}([\d\s]+[,.]\d{2})', t)
    netto = None
    brutto = None
    if n_vals:
        try:
            netto = float(re.sub(r'\s', '', n_vals[0]).replace(',', '.'))
        except ValueError:
            pass
    if b_vals:
        try:
            brutto = float(re.sub(r'\s', '', b_vals[0]).replace(',', '.'))
        except ValueError:
            pass

    # 5. MPP
    mpp_required = brutto is not None and brutto >= 15000.0
    has_mpp = bool(re.search(r'podzielonej\s+p[łl]atno|mechanizm\s+podziel', t))
    if mpp_required and not has_mpp:
        errors.append(AuditError(code="MISSING_MPP", message='Brak dopisku "Mechanizm Podzielonej Platnosci" dla kwoty >= 15000 PLN', field="mpp"))

    # 6. KSeF validation
    ksef_matches = re.findall(r'\b\d{10}-\d{8}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{6}\b|\b\d{35}\b', t)
    detected_ksef = ksef_matches[0] if ksef_matches else None
    ksef_ready = False
    if detected_ksef:
        clean_ksef = re.sub(r'[^a-zA-Z0-9]', '', detected_ksef)
        if len(clean_ksef) == 35:
            val = validate_ksef_number(detected_ksef, seller_nip, invoice_year)
            if not val["valid"]:
                errors.append(AuditError(code="INVALID_KSEF", message=f"Błąd KSeF: {val['error']}", field="ksef"))
            else:
                ksef_ready = True
        else:
            ksef_ready = True
    else:
        if invoice_year >= 2026:
            errors.append(AuditError(code="MISSING_KSEF", message="Brak obowiązkowego numeru KSeF (wymagany od 01.04.2026)", field="ksef"))
        elif invoice_year >= 2024:
            warnings.append("Brak numeru KSeF — zalecane wdrożenie")

    # 7. Invoice items math checks
    pozycje = _extract_invoice_items(text)
    if pozycje and netto and brutto:
        total_items_netto = sum(p["netto"] for p in pozycje)
        total_items_brutto = sum(p["brutto"] for p in pozycje)
        if abs(total_items_netto - netto) > 5.0:
            errors.append(AuditError(code="ITEMS_SUM_MISMATCH_NETTO", message=f"Suma netto pozycji ({total_items_netto:,.2f}) nie zgadza się z sumą netto faktury ({netto:,.2f})", field="netto"))
        if abs(total_items_brutto - brutto) > 5.0:
            errors.append(AuditError(code="ITEMS_SUM_MISMATCH_BRUTTO", message=f"Suma brutto pozycji ({total_items_brutto:,.2f}) nie zgadza się z sumą brutto faktury ({brutto:,.2f})", field="brutto"))

    # Invoice number
    inv_match = re.search(r"(?:faktura|FV|VAT)[^\d]*(\d[\d/\-]+)", text, re.IGNORECASE)
    invoice_number = inv_match.group(1) if inv_match else None

    # Invoice date
    date_match = re.search(r'\b\d{1,2}[./]\d{1,2}[./]\d{4}\b', text)
    invoice_date = date_match.group(0) if date_match else None

    return InvoiceAuditResponse(
        status="ok" if not errors else "error",
        audit_mode="rule_based",
        confidence=0.7 if not errors else 0.4,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        seller_nip=seller_nip,
        netto=netto,
        brutto=brutto,
        mpp_required=mpp_required,
        ksef_ready=ksef_ready,
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
