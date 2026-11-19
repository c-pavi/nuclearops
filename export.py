# export.py
# Exports the results of a view to CSV (using pandas) or PDF (using fpdf2).

import io
from datetime import date
import pandas as pd
from fpdf import FPDF


def to_csv(rows):
    """Turn a list of row dictionaries into CSV text."""
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def to_pdf(title, rows):
    """Turn a list of row dictionaries into a simple PDF table. Returns the PDF as bytes."""
    pdf = FPDF(orientation="L", unit="mm", format="Letter")   # landscape fits wide tables
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "NuclearOps - " + title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Exported on " + date.today().isoformat() + "  |  " + str(len(rows)) + " rows",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    if not rows:
        pdf.cell(0, 8, "This view returned no rows.")
        return bytes(pdf.output())

    columns = list(rows[0].keys())
    col_width = pdf.epw / len(columns)     # epw = usable page width

    # Header row
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(220, 230, 242)
    for col in columns:
        pdf.cell(col_width, 7, col.replace("_", " ").title()[:22], border=1, fill=True)
    pdf.ln()

    # Data rows (long text is cut off so each row stays one line high)
    pdf.set_font("Helvetica", "", 8)
    max_chars = int(col_width / 1.7)
    for row in rows:
        for col in columns:
            value = "" if row[col] is None else str(row[col])
            pdf.cell(col_width, 6, value[:max_chars], border=1)
        pdf.ln()

    return bytes(pdf.output())
