"""Core PDF operations using PyMuPDF (fitz)."""
import os
import hashlib
import subprocess
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageEnhance
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm


# ─── Compress ────────────────────────────────────────────────────────────────

def compress_pdf(input_path: str, output_path: str, quality: int = 75) -> dict:
    """Compress a PDF. quality 0-100 (higher = better quality, larger file)."""
    doc = fitz.open(input_path)
    # Rewrite images at reduced quality
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n > 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix.tobytes("jpeg", jpg_quality=quality)
                doc.update_stream(xref, img_data)
            except Exception:
                pass

    doc.save(
        output_path,
        garbage=4,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
    )
    doc.close()

    orig_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    return {
        "original_size": orig_size,
        "compressed_size": new_size,
        "ratio": round((1 - new_size / orig_size) * 100, 1) if orig_size else 0,
    }


# ─── Split ────────────────────────────────────────────────────────────────────

def split_pdf(input_path: str, output_dir: str, ranges: list[tuple[int, int]] | None = None) -> list[str]:
    """
    Split PDF into individual pages or specified ranges.
    ranges: list of (start, end) 1-based inclusive. None = one file per page.
    """
    doc = fitz.open(input_path)
    total = len(doc)
    stem = Path(input_path).stem
    outputs = []

    if ranges is None:
        ranges = [(i + 1, i + 1) for i in range(total)]

    for start, end in ranges:
        start = max(1, start)
        end = min(total, end)
        out_doc = fitz.open()
        out_doc.insert_pdf(doc, from_page=start - 1, to_page=end - 1)
        out_path = os.path.join(output_dir, f"{stem}_p{start}-{end}.pdf")
        out_doc.save(out_path)
        out_doc.close()
        outputs.append(out_path)

    doc.close()
    return outputs


# ─── Merge ────────────────────────────────────────────────────────────────────

def merge_pdfs(input_paths: list[str], output_path: str) -> str:
    out_doc = fitz.open()
    for path in input_paths:
        doc = fitz.open(path)
        out_doc.insert_pdf(doc)
        doc.close()
    out_doc.save(output_path, garbage=4, deflate=True)
    out_doc.close()
    return output_path


# ─── Rotate ───────────────────────────────────────────────────────────────────

def rotate_pages(input_path: str, output_path: str, page_rotations: dict[int, int]) -> str:
    """
    Rotate pages. page_rotations: {page_index_0based: degrees (90/180/270)}
    """
    doc = fitz.open(input_path)
    for page_idx, degrees in page_rotations.items():
        if 0 <= page_idx < len(doc):
            page = doc[page_idx]
            page.set_rotation((page.rotation + degrees) % 360)
    doc.save(output_path)
    doc.close()
    return output_path


# ─── Rearrange pages ──────────────────────────────────────────────────────────

def rearrange_pages(input_path: str, output_path: str, new_order: list[int]) -> str:
    """new_order: list of 0-based page indices in desired order."""
    doc = fitz.open(input_path)
    doc.select(new_order)
    doc.save(output_path)
    doc.close()
    return output_path


# ─── Remove duplicates ────────────────────────────────────────────────────────

def _page_hash(page: fitz.Page) -> str:
    pix = page.get_pixmap(dpi=72)
    return hashlib.md5(pix.samples).hexdigest()


def remove_duplicate_pages(input_path: str, output_path: str) -> dict:
    doc = fitz.open(input_path)
    seen = {}
    keep = []
    removed = []

    for i, page in enumerate(doc):
        h = _page_hash(page)
        if h not in seen:
            seen[h] = i
            keep.append(i)
        else:
            removed.append(i + 1)

    doc.select(keep)
    doc.save(output_path)
    doc.close()
    return {"kept": len(keep), "removed": removed}


# ─── PDF to Images ────────────────────────────────────────────────────────────

def pdf_to_images(input_path: str, output_dir: str, dpi: int = 150, fmt: str = "png") -> list[str]:
    doc = fitz.open(input_path)
    stem = Path(input_path).stem
    outputs = []
    for i, page in enumerate(doc):
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        out_path = os.path.join(output_dir, f"{stem}_page{i + 1}.{fmt}")
        pix.save(out_path)
        outputs.append(out_path)
    doc.close()
    return outputs


# ─── PDF to Text ──────────────────────────────────────────────────────────────

def pdf_to_text(input_path: str, output_path: str | None = None) -> str:
    doc = fitz.open(input_path)
    text_parts = []
    for i, page in enumerate(doc):
        text_parts.append(f"--- Page {i + 1} ---\n")
        text_parts.append(page.get_text())
        text_parts.append("\n")
    doc.close()
    full_text = "\n".join(text_parts)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
    return full_text


# ─── Images to PDF ────────────────────────────────────────────────────────────

def images_to_pdf(image_paths: list[str], output_path: str, page_size: tuple = A4) -> str:
    out_doc = fitz.open()
    for img_path in image_paths:
        img_doc = fitz.open(img_path)
        rect = img_doc[0].rect
        pdf_bytes = img_doc.convert_to_pdf()
        img_doc.close()
        img_pdf = fitz.open("pdf", pdf_bytes)
        out_doc.insert_pdf(img_pdf)
    out_doc.save(output_path)
    out_doc.close()
    return output_path


# ─── Text to PDF ──────────────────────────────────────────────────────────────

def text_to_pdf(text: str, output_path: str, font_size: int = 11, title: str = "") -> str:
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []
    if title:
        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 0.5*cm))

    style = styles["Normal"]
    style.fontSize = font_size
    style.leading = font_size * 1.4

    for line in text.split("\n"):
        if line.strip():
            story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style))
        else:
            story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    return output_path


# ─── Word / Excel to PDF (via LibreOffice) ───────────────────────────────────

def _libreoffice_convert(input_path: str, output_dir: str) -> str:
    """Convert using LibreOffice headless. Requires LibreOffice installed."""
    cmd = [
        "libreoffice", "--headless", "--convert-to", "pdf",
        "--outdir", output_dir, input_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice error: {result.stderr}")
    stem = Path(input_path).stem
    return os.path.join(output_dir, f"{stem}.pdf")


def word_to_pdf(input_path: str, output_path: str) -> str:
    out_dir = os.path.dirname(output_path)
    result_path = _libreoffice_convert(input_path, out_dir)
    expected = os.path.join(out_dir, Path(input_path).stem + ".pdf")
    if os.path.exists(expected) and expected != output_path:
        os.rename(expected, output_path)
    return output_path


def excel_to_pdf(input_path: str, output_path: str) -> str:
    return word_to_pdf(input_path, output_path)


# ─── Sign PDF ─────────────────────────────────────────────────────────────────

def sign_pdf(input_path: str, output_path: str, signature_image_path: str,
             page_index: int = 0, x: float = 50, y: float = 700,
             width: float = 200, height: float = 80) -> str:
    """Embed a signature image onto a PDF page."""
    doc = fitz.open(input_path)
    page = doc[page_index]
    rect = fitz.Rect(x, y, x + width, y + height)
    page.insert_image(rect, filename=signature_image_path)
    doc.save(output_path)
    doc.close()
    return output_path


# ─── Image editing (pre-PDF) ──────────────────────────────────────────────────

def edit_image(input_path: str, output_path: str,
               brightness: float = 1.0, contrast: float = 1.0,
               sharpness: float = 1.0, rotation: int = 0,
               grayscale: bool = False) -> str:
    img = Image.open(input_path)
    if rotation:
        img = img.rotate(-rotation, expand=True)
    if grayscale:
        img = img.convert("L").convert("RGB")
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if sharpness != 1.0:
        img = ImageEnhance.Sharpness(img).enhance(sharpness)
    img.save(output_path)
    return output_path


def get_pdf_page_thumbnails(input_path: str, dpi: int = 72, max_pages: int = 100) -> list:
    """Return list of PIL Images for each page (for UI display)."""
    doc = fitz.open(input_path)
    thumbs = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        thumbs.append(img)
    doc.close()
    return thumbs


def get_pdf_info(input_path: str) -> dict:
    doc = fitz.open(input_path)
    info = {
        "pages": len(doc),
        "size_bytes": os.path.getsize(input_path),
        "metadata": doc.metadata,
    }
    doc.close()
    return info
