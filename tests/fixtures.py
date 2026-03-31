from __future__ import annotations

from pathlib import Path

from reportlab.pdfgen import canvas


def write_pdf(path: Path, page_texts: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))
    for text in page_texts:
        if text:
            y = 780
            for line in text.split("\n"):
                pdf.drawString(72, y, line)
                y -= 18
        pdf.showPage()
    pdf.save()


def create_synthetic_pdf_corpus(root: Path) -> Path:
    comps = root / "comps"
    memo = root / "offering_memo"
    write_pdf(
        comps / "comp_a.pdf",
        [
            "CONFIDENTIAL REPORT\nDowntown Tower NOI: $ 1,200,000\nCap rate is 6.1%\nPage 1 of 2",
            "CONFIDENTIAL REPORT\nStable rent growth signal\nPage 2 of 2",
        ],
    )
    write_pdf(
        memo / "memo_a.pdf",
        ["MEMO HEADER\nSuburban Retail occupancy at 94% on 3/7/2025\nPage 1 of 1"],
    )
    return root
