"""
Synapsa — Invoice History (SQLite)
Persystentna historia faktur — przeżywa restarty aplikacji.

Użycie:
    from synapsa.agents.invoice_history import InvoiceHistory
    db = InvoiceHistory()
    db.save(result, sprzedawca="Firma X", nabywca="Jan Kowalski")
    rows = db.get_all()          # lista słowników
    db.delete(invoice_nr)
"""
import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Lokalizacja bazy — obok synapsa_workspace, niezależna od CWD
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.abspath(os.path.join(_MODULE_DIR, "..", "..", "synapsa_workspace"))
_DB_PATH = os.path.join(_WORKSPACE_DIR, "invoice_history.db")

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS invoices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nr          TEXT NOT NULL UNIQUE,
    typ_pracy   TEXT,
    netto       REAL,
    vat_rate    INTEGER,
    vat_kwota   REAL,
    brutto      REAL,
    mpp         INTEGER DEFAULT 0,
    sprzedawca  TEXT,
    nabywca     TEXT,
    invoice_date TEXT,
    created_at  TEXT,
    raw_json    TEXT
);
"""


class InvoiceHistory:
    """Persystentna historia faktur w SQLite."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or _DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Tworzy tabelę jeśli nie istnieje."""
        with self._connect() as conn:
            conn.execute(_CREATE_SQL)
            conn.commit()

    def save(self, result: dict, sprzedawca: str = "", nabywca: str = "") -> bool:
        """
        Zapisuje wynik ZlecenieProcessor.process() do historii.

        Args:
            result: dict z ZlecenieProcessor.process() (status='success')
            sprzedawca: dane sprzedawcy (opcjonalne)
            nabywca: dane nabywcy (opcjonalne)

        Returns:
            True jeśli zapisano, False jeśli duplikat lub błąd
        """
        if result.get("status") != "success":
            return False

        calc = result.get("calc", {})
        parse = result.get("parse", {})
        nr = result.get("invoice_nr", "")

        row = {
            "nr": nr,
            "typ_pracy": parse.get("typ_pracy", ""),
            "netto": calc.get("netto", 0.0),
            "vat_rate": calc.get("vat_rate", 23),
            "vat_kwota": calc.get("vat_kwota", 0.0),
            "brutto": calc.get("brutto", 0.0),
            "mpp": 1 if calc.get("mpp_required") else 0,
            "sprzedawca": sprzedawca or "",
            "nabywca": nabywca or "",
            "invoice_date": result.get("invoice_date", ""),
            "created_at": datetime.now().isoformat(),
            "raw_json": json.dumps(result, ensure_ascii=False),
        }

        try:
            with self._connect() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO invoices
                    (nr, typ_pracy, netto, vat_rate, vat_kwota, brutto, mpp,
                     sprzedawca, nabywca, invoice_date, created_at, raw_json)
                    VALUES
                    (:nr, :typ_pracy, :netto, :vat_rate, :vat_kwota, :brutto, :mpp,
                     :sprzedawca, :nabywca, :invoice_date, :created_at, :raw_json)
                """, row)
                conn.commit()
                return conn.execute(
                    "SELECT changes()"
                ).fetchone()[0] > 0
        except Exception as e:
            logger.error(f"InvoiceHistory.save() error: {e}")
            return False

    def get_all(self, limit: int = 100) -> list:
        """Zwraca wszystkie faktury (najnowsze pierwsze)."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM invoices ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"InvoiceHistory.get_all() error: {e}")
            return []

    def delete(self, invoice_nr: str) -> bool:
        """Usuwa fakturę z historii po numerze."""
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM invoices WHERE nr = ?", (invoice_nr,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"InvoiceHistory.delete() error: {e}")
            return False

    def get_stats(self) -> dict:
        """Zwraca statystyki: liczba faktur, suma brutto, w tym MPP."""
        try:
            with self._connect() as conn:
                row = conn.execute("""
                    SELECT
                        COUNT(*) as count,
                        COALESCE(SUM(brutto), 0.0) as total_brutto,
                        COALESCE(SUM(netto), 0.0) as total_netto,
                        SUM(mpp) as mpp_count
                    FROM invoices
                """).fetchone()
                return dict(row)
        except Exception as e:
            logger.error(f"InvoiceHistory.get_stats() error: {e}")
            return {"count": 0, "total_brutto": 0.0, "total_netto": 0.0, "mpp_count": 0}

    def count(self) -> int:
        """Szybki licznik faktur w bazie."""
        try:
            with self._connect() as conn:
                return conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        except Exception:
            return 0
