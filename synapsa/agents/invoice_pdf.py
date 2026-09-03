"""
Synapsa — PDF Invoice Generator
Generuje profesjonalne faktury VAT w formacie PDF używając reportlab.

Użycie:
    from synapsa.agents.invoice_pdf import generate_invoice_pdf
    result = processor.process("kostka brukowa 100m2, 150 PLN/m2")
    pdf_bytes = generate_invoice_pdf(result)
    # pdf_bytes → st.download_button() / open("faktura.pdf", "wb").write(pdf_bytes)
"""
import io


def generate_invoice_pdf(result: dict) -> bytes:
    """
    Generuje PDF faktury VAT z danych ZlecenieProcessor.process().

    Args:
        result: dict zwrócony przez ZlecenieProcessor.process() ze status='success'

    Returns:
        bytes — zawartość pliku PDF gotowa do zapisu lub streamingu.

    Raises:
        ImportError: jeśli reportlab nie jest zainstalowany
        ValueError: jeśli result.status != 'success'
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise ImportError(
            "reportlab nie jest zainstalowany. Uruchom: pip install reportlab\n"
            "lub: pip install synapsa (zawiera reportlab w zależnościach)"
        )

    if result.get("status") != "success":
        raise ValueError(f"Nie można wygenerować PDF — status: {result.get('error', 'nieznany błąd')}")

    calc = result["calc"]
    parse = result["parse"]
    nr = result["invoice_nr"]
    today = result["invoice_date"]
    nabywca = result.get("nabywca", "") or ""
    sprzedawca = result.get("sprzedawca", "") or ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Style
    title_style = ParagraphStyle(
        "invoice_title",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#FF5722"),
        spaceAfter=4,
        leading=24,
    )
    sub_style = ParagraphStyle(
        "invoice_sub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=2,
    )
    cell_style = ParagraphStyle(
        "invoice_cell",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )

    story = []

    # ── NAGŁÓWEK ──────────────────────────────────────────────────────────
    story.append(Paragraph("FAKTURA VAT", title_style))
    story.append(Paragraph(
        f"Nr: <b>{nr}</b> &nbsp;&nbsp;&nbsp; Data wystawienia: <b>{today}</b>",
        sub_style,
    ))
    story.append(Spacer(1, 0.5 * cm))

    # ── STRONY: SPRZEDAWCA / NABYWCA ──────────────────────────────────────
    sprzedawca_html = (sprzedawca or "[TWOJA FIRMA]<br/>[NIP: ]<br/>[ADRES]").replace("\n", "<br/>")
    nabywca_html = (nabywca or "[FIRMA / OSOBA NABYWCA]<br/>[NIP: ]<br/>[ADRES]").replace("\n", "<br/>")

    parties_data = [
        [Paragraph("<b>SPRZEDAWCA</b>", cell_style), Paragraph("<b>NABYWCA</b>", cell_style)],
        [Paragraph(sprzedawca_html, cell_style), Paragraph(nabywca_html, cell_style)],
    ]
    parties_table = Table(parties_data, colWidths=[8.5 * cm, 8.5 * cm])
    parties_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── TABELA POZYCJI ────────────────────────────────────────────────────
    typ = parse["typ_pracy"].title()
    ilosc = calc["pozycje"][0]["ilosc"]
    jednostka = calc["jednostka"]
    cena_j = calc["cena_m2"]
    netto = calc["netto"]
    mat = calc["materialy_netto"]
    rob = calc["robocizna_netto"]

    items_data = [
        ["Lp", "Opis usługi / towaru", "Jed.", "Ilość", "Cena netto", "Wartość netto"],
        ["1", typ, jednostka, f"{ilosc:.0f}", f"{cena_j:,.2f} PLN", f"{netto:,.2f} PLN"],
        ["", "  \u21b3 materiały (szacunek)", "", "", "", f"{mat:,.2f} PLN"],
        ["", "  \u21b3 robocizna (szacunek)", "", "", "", f"{rob:,.2f} PLN"],
    ]
    col_widths = [0.8 * cm, 6.4 * cm, 1.4 * cm, 1.4 * cm, 3.0 * cm, 3.5 * cm]
    items_table = Table(items_data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF5722")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#EEEEEE")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF8F5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── PODSUMOWANIE ──────────────────────────────────────────────────────
    vat_rate = calc["vat_rate"]
    vat_kwota = calc["vat_kwota"]
    brutto = calc["brutto"]
    mpp = calc["mpp_required"]

    sum_rows = [
        ["Wartość netto:", f"{netto:,.2f} PLN"],
        [f"VAT {vat_rate}%:", f"{vat_kwota:,.2f} PLN"],
        ["DO ZAPŁATY:", f"{brutto:,.2f} PLN"],
    ]
    if mpp:
        sum_rows.append(["⚠  Mechanizm podzielonej płatności", "OBOWIĄZKOWY"])

    sum_table = Table(sum_rows, colWidths=[10 * cm, 7 * cm])
    sum_style = [
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 2), (-1, 2), 13),
        ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#FF5722")),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#FFF3E0")),
        ("BOX", (0, 2), (-1, 2), 1.2, colors.HexColor("#FF5722")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if mpp:
        sum_style += [
            ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FFF9C4")),
            ("TEXTCOLOR", (0, 3), (-1, 3), colors.HexColor("#B71C1C")),
            ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
            ("FONTSIZE", (0, 3), (-1, 3), 9),
        ]
    sum_table.setStyle(TableStyle(sum_style))
    story.append(sum_table)
    story.append(Spacer(1, 1.0 * cm))

    # ── STOPKA ────────────────────────────────────────────────────────────
    story.append(Paragraph("Forma płatności: przelew bankowy 14 dni", sub_style))
    story.append(Paragraph("Nr konta: [NUMER KONTA BANKOWEGO]", sub_style))
    story.append(Spacer(1, 1.5 * cm))

    sigs_table = Table(
        [["Wystawił: ___________________", "Zatwierdził: ___________________"]],
        colWidths=[8.5 * cm, 8.5 * cm],
    )
    story.append(sigs_table)

    doc.build(story)
    return buffer.getvalue()
