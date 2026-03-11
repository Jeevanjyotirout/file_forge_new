"""
FileForge – Converter Service
Handles all file conversion / processing operations.
"""
import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Supported operations ──────────────────────────────────────────────────────
SUPPORTED_OPERATIONS = {
    # Passthrough / basic
    "copy":         "Copy file as-is",
    # Image operations
    "compress-img": "Compress image",
    "img-to-pdf":   "Image to PDF",
    # Document operations
    "pdf-to-txt":   "Extract text from PDF",
    # Archive
    "zip":          "Zip file",
}


def convert_file(
    input_path: str,
    output_base_path: str,
    operation: str,
    original_name: str,
) -> str:
    """
    Dispatch to the correct conversion handler.
    Returns the path to the output file.
    """
    ext = Path(original_name).suffix.lower()
    logger.info(f"convert_file | op={operation} | input={input_path} | ext={ext}")

    handlers = {
        "copy":         _op_copy,
        "compress-img": _op_compress_image,
        "img-to-pdf":   _op_image_to_pdf,
        "pdf-to-txt":   _op_pdf_to_txt,
        "zip":          _op_zip,
    }

    handler = handlers.get(operation, _op_copy)
    result  = handler(input_path, output_base_path, original_name)
    logger.info(f"convert_file | result={result}")
    return result


# ── Handlers ──────────────────────────────────────────────────────────────────

def _op_copy(input_path: str, output_base: str, original_name: str) -> str:
    """Simply copy the file to output directory."""
    ext    = Path(original_name).suffix
    output = output_base + ext
    shutil.copy2(input_path, output)
    return output


def _op_compress_image(input_path: str, output_base: str, original_name: str) -> str:
    """Compress image using Pillow."""
    try:
        from PIL import Image
        ext    = Path(original_name).suffix.lower()
        output = output_base + ext

        img = Image.open(input_path)
        # Convert RGBA → RGB for JPEG
        if ext in (".jpg", ".jpeg") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        save_kwargs = {}
        if ext in (".jpg", ".jpeg"):
            save_kwargs = {"quality": 75, "optimize": True}
        elif ext == ".png":
            save_kwargs = {"optimize": True, "compress_level": 7}
        elif ext == ".webp":
            save_kwargs = {"quality": 75, "method": 6}

        img.save(output, **save_kwargs)
        logger.info(f"Compressed image: {input_path} → {output}")
        return output
    except ImportError:
        logger.warning("Pillow not available, falling back to copy")
        return _op_copy(input_path, output_base, original_name)
    except Exception as e:
        logger.error(f"Image compress failed: {e}")
        return _op_copy(input_path, output_base, original_name)


def _op_image_to_pdf(input_path: str, output_base: str, original_name: str) -> str:
    """Convert image to PDF using Pillow."""
    try:
        from PIL import Image
        output = output_base + ".pdf"
        img    = Image.open(input_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output, "PDF", resolution=100)
        logger.info(f"Image → PDF: {input_path} → {output}")
        return output
    except ImportError:
        logger.warning("Pillow not available for img-to-pdf, falling back to copy")
        return _op_copy(input_path, output_base, original_name)
    except Exception as e:
        logger.error(f"img-to-pdf failed: {e}")
        return _op_copy(input_path, output_base, original_name)


def _op_pdf_to_txt(input_path: str, output_base: str, original_name: str) -> str:
    """Extract text from PDF using pdfplumber or PyPDF2."""
    output = output_base + ".txt"
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        with open(output, "w", encoding="utf-8") as f:
            f.write("\n\n".join(text_parts))
        logger.info(f"PDF → TXT: {input_path} → {output}")
        return output
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"pdfplumber failed: {e}")

    # Fallback: pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(input_path)
        text_parts = [p.extract_text() or "" for p in reader.pages]
        with open(output, "w", encoding="utf-8") as f:
            f.write("\n\n".join(text_parts))
        return output
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"pypdf failed: {e}")

    # Final fallback – write error message
    with open(output, "w") as f:
        f.write("PDF text extraction not available. Install pdfplumber or pypdf.\n")
    return output


def _op_zip(input_path: str, output_base: str, original_name: str) -> str:
    """Zip a single file."""
    import zipfile
    output = output_base + ".zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(input_path, arcname=original_name)
    logger.info(f"Zipped: {input_path} → {output}")
    return output
