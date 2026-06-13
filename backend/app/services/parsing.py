import io
import copy
import fitz  # PyMuPDF
from PIL import Image
from app.services.ai import AIPipeline
from app.services.normalization import normalize_skills_list, extract_skills_from_text

UNCERTAINTY_THRESHOLD = 0.8


async def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, float]:
    """
    Extract text from a PDF using PyMuPDF.
    Returns (text, layout_complexity_score).
    layout_complexity: 0.0 = simple single-column, 1.0 = highly complex.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    total_images = 0
    multi_column_pages = 0
    total_pages = len(doc)

    for page in doc:
        text += page.get_text()
        blocks = page.get_text("blocks")
        # Heuristic: >2 blocks with text on same y-range suggests multi-column
        if len(blocks) > 2:
            multi_column_pages += 1
        total_images += len(page.get_images())

    # Complexity scoring
    image_density = min(1.0, total_images / max(1, total_pages * 3))
    column_density = multi_column_pages / max(1, total_pages)
    layout_complexity = round(0.4 * image_density + 0.6 * column_density, 2)

    return text.strip(), layout_complexity


async def extract_text_from_docx(file_bytes: bytes) -> tuple[str, float]:
    """
    Extract text from a DOCX file using built-in zipfile and XML parsing.
    Returns (text, layout_complexity_score).
    """
    import zipfile
    import xml.etree.ElementTree as ET
    try:
        doc = zipfile.ZipFile(io.BytesIO(file_bytes))
        xml_content = doc.read('word/document.xml')
        tree = ET.XML(xml_content)
        # Extract text from all nodes, adding newlines for paragraphs
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text = '\n'.join(node.text for node in tree.findall('.//w:t', namespace) if node.text)
        return text.strip(), 0.1
    except Exception as e:
        return f"DOCX parsing error: {str(e)}", 1.0


async def extract_text_from_image(file_bytes: bytes) -> tuple[str, float]:
    """
    Extract text from an image using EasyOCR.
    Returns (text, layout_complexity_score).
    """
    try:
        import easyocr
        import numpy as np
        image = Image.open(io.BytesIO(file_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        reader = easyocr.Reader(['en'])
        result = reader.readtext(np.array(image))
        text = " ".join([text for (bbox, text, prob) in result])
        
        if not text.strip():
            return "OCR failed to extract readable text. Image may be blurry or low resolution.", 1.0
            
        return text.strip(), 0.9
    except Exception as e:
        return f"OCR processing error: {str(e)}. Ensure EasyOCR is installed.", 1.0


async def parse_resume_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Full resume parsing pipeline:
    1. Extract text (PDF or image)
    2. AI structured extraction
    3. Skill taxonomy normalization
    Returns complete parsed_resume dict with _meta.
    """
    # Step 1: Text extraction
    if filename.lower().endswith(".pdf"):
        text, layout_complexity = await extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        text, layout_complexity = await extract_text_from_docx(file_bytes)
    else:
        text, layout_complexity = await extract_text_from_image(file_bytes)

    if not text:
        raise ValueError("Could not extract any text from the document")

    # Step 2: AI structured extraction
    parsed = await AIPipeline.parse_resume(text)

    # Step 3: Normalize skills through ontology
    if "skills" in parsed:
        raw_skills = copy.deepcopy(parsed["skills"])
        normalized_skills = normalize_skills_list(copy.deepcopy(parsed["skills"]))
        parsed["skills"] = [{"name": s["name"], "type": s.get("type", "hard")} for s in normalized_skills]
        parsed["normalized_skills"] = normalized_skills
        parsed["raw_extracted_skills"] = raw_skills
        parsed["scoring_skills"] = [s for s in normalized_skills if s.get("is_scoring_eligible", True)]
        parsed["negated_skills"] = [s for s in normalized_skills if s.get("negated", False)]

    # Step 4: Attach parsing metadata (for calibrated uncertainty UI)
    extraction_confidence = _compute_extraction_confidence(layout_complexity)
    raw_extracted_text = text if extraction_confidence < UNCERTAINTY_THRESHOLD else ""
    parsed["_meta"] = {
        "layout_complexity": layout_complexity,
        "extraction_confidence": extraction_confidence,
        "parser_warnings": _generate_warnings(layout_complexity, parsed),
        "raw_extracted_text": raw_extracted_text,
    }

    return parsed


def _generate_warnings(layout_complexity: float, parsed: dict) -> list[str]:
    """Generate human-readable warnings about parsing quality."""
    warnings = []
    if layout_complexity > 0.6:
        warnings.append("Detected multi-column or image-heavy layout. Some sections may be misordered. Verify raw text extraction.")
    if layout_complexity > 0.8:
        warnings.append("High formatting complexity detected. Skill extraction confidence is low. Please review extracted skills manually.")
    return warnings


def _compute_extraction_confidence(layout_complexity: float) -> float:
    """
    Calibrate extraction confidence from layout complexity.
    Keeps confidence conservative for complex, decorative resumes.
    """
    confidence = 1.0 - (0.35 * max(0.0, min(layout_complexity, 1.0)))
    return round(max(0.55, confidence), 2)