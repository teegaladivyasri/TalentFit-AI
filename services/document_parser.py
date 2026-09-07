"""Document Parser Service.

Extracts sanitized plaintext and structural content from PDF, DOCX, and TXT files.
Handles corrupted files, password-protected/empty documents, and various character encodings gracefully.
"""

import io
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union, BinaryIO, Tuple

# Security & Memory Protection limit: 500,000 characters (~100,000 words / ~200 pages)
MAX_EXTRACTED_TEXT_LENGTH = 500_000


class DocumentParser:
    """Service responsible for extracting plain text and metadata from uploaded documents."""

    def __init__(self):
        pass

    @staticmethod
    def _sanitize_text(raw_text: str) -> str:
        """Clean and normalize extracted text while preserving section boundaries."""
        if not raw_text:
            return ""
        
        # Enforce maximum text length bound
        if len(raw_text) > MAX_EXTRACTED_TEXT_LENGTH:
            raw_text = raw_text[:MAX_EXTRACTED_TEXT_LENGTH]
        
        # Strip null bytes and non-printable control characters (except newline, tab, carriage return)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text)
        
        # Standardize carriage returns to standard newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Replace multiple consecutive spaces/tabs with single space on each line
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        
        # Collapse excessive empty lines (maximum 2 consecutive blank lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        return cleaned_text.strip()

    @staticmethod
    def _get_bytes(file_input: Union[bytes, BinaryIO, Any]) -> bytes:
        """Helper to safely extract raw bytes from various input types."""
        if isinstance(file_input, bytes):
            return file_input
        elif hasattr(file_input, "getvalue"):
            # Streamlit UploadedFile or io.BytesIO
            return file_input.getvalue()
        elif hasattr(file_input, "read"):
            # Standard file-like object
            content = file_input.read()
            if hasattr(file_input, "seek"):
                file_input.seek(0)
            if isinstance(content, str):
                return content.encode("utf-8")
            return content
        return b""

    def extract_text_from_pdf(self, file_input: Union[bytes, BinaryIO, Any]) -> Tuple[str, int, Optional[str]]:
        """Extract plain text and page count from a PDF document using pypdf.
        
        Returns:
            Tuple of (extracted_text, page_count, error_message)
        """
        file_bytes = self._get_bytes(file_input)
        if not file_bytes:
            return "", 0, "PDF document is empty (0 bytes)."

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            
            if reader.is_encrypted:
                try:
                    # Attempt empty password decryption
                    reader.decrypt("")
                except Exception:
                    return "", 0, "PDF document is password-protected and cannot be read."

            page_count = len(reader.pages)
            if page_count == 0:
                return "", 0, "PDF document has no pages."

            extracted_pages = []
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        extracted_pages.append(page_text)
                except Exception:
                    continue

            full_text = "\n\n".join(extracted_pages)
            cleaned = self._sanitize_text(full_text)
            
            if not cleaned:
                return "", page_count, "PDF document contains no extractable text (it may be a scanned image)."
                
            return cleaned, page_count, None

        except Exception:
            return "", 0, "Unable to parse PDF document. Please verify it is a valid, uncorrupted, and unencrypted PDF file."

    def extract_text_from_docx(self, file_input: Union[bytes, BinaryIO, Any]) -> Tuple[str, int, Optional[str]]:
        """Extract plain text from a DOCX document including paragraphs and tables.
        
        Returns:
            Tuple of (extracted_text, paragraph_count, error_message)
        """
        file_bytes = self._get_bytes(file_input)
        if not file_bytes:
            return "", 0, "DOCX document is empty (0 bytes)."

        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            
            text_blocks = []
            
            # Extract paragraphs
            for p in doc.paragraphs:
                p_text = p.text.strip()
                if p_text:
                    text_blocks.append(p_text)
                    
            # Extract table cells
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        text_blocks.append(" | ".join(row_cells))

            full_text = "\n".join(text_blocks)
            cleaned = self._sanitize_text(full_text)
            
            if not cleaned:
                return "", len(doc.paragraphs), "DOCX document contains no readable text."
                
            return cleaned, len(doc.paragraphs), None

        except Exception:
            return "", 0, "Unable to parse DOCX document. Please verify it is a valid, uncorrupted Word document."

    def extract_text_from_txt(self, file_input: Union[bytes, BinaryIO, str, Any]) -> Tuple[str, int, Optional[str]]:
        """Extract plain text from TXT data supporting multiple encodings.
        
        Returns:
            Tuple of (extracted_text, line_count, error_message)
        """
        if isinstance(file_input, str):
            cleaned = self._sanitize_text(file_input)
            if not cleaned:
                return "", 0, "Text content is empty."
            return cleaned, len(cleaned.splitlines()), None

        file_bytes = self._get_bytes(file_input)
        if not file_bytes:
            return "", 0, "Text file is empty (0 bytes)."

        # Try common text encodings
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
        decoded_text = None

        for enc in encodings:
            try:
                decoded_text = file_bytes.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if decoded_text is None:
            # Fallback with replacement of invalid characters
            decoded_text = file_bytes.decode("utf-8", errors="replace")

        cleaned = self._sanitize_text(decoded_text)
        if not cleaned:
            return "", 0, "Text file contains no readable characters."

        return cleaned, len(cleaned.splitlines()), None

    def extract_text_from_file(self, file_obj: Any, filename: Optional[str] = None) -> str:
        """High-level dispatcher extracting plaintext from a file object or path."""
        res = self.parse_document(file_obj, filename=filename)
        return res.get("text", "")

    def parse_document(self, uploaded_file: Any, filename: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive document parser returning sanitized text, statistics, and health status."""
        if uploaded_file is None:
            return {
                "filename": "",
                "text": "",
                "char_count": 0,
                "word_count": 0,
                "page_count": 0,
                "status": "empty",
                "error_message": "No document provided."
            }

        raw_name = (
            filename or 
            getattr(uploaded_file, "name", "") or 
            (uploaded_file if isinstance(uploaded_file, str) else "unnamed_document")
        )
        # Strip directory traversal characters to preserve safe display filename
        resolved_name = Path(raw_name).name if raw_name else "unnamed_document"
        
        ext = resolved_name.split(".")[-1].lower() if "." in resolved_name else ""
        
        text = ""
        count = 0
        error_msg = None

        if ext == "pdf":
            text, count, error_msg = self.extract_text_from_pdf(uploaded_file)
        elif ext == "docx":
            text, count, error_msg = self.extract_text_from_docx(uploaded_file)
        elif ext in ["txt", "text", "md"]:
            text, count, error_msg = self.extract_text_from_txt(uploaded_file)
        else:
            return {
                "filename": resolved_name,
                "text": "",
                "char_count": 0,
                "word_count": 0,
                "page_count": 0,
                "status": "error",
                "error_message": f"Unsupported file format (.{ext}). Supported formats: PDF, DOCX, TXT."
            }

        if error_msg:
            return {
                "filename": resolved_name,
                "text": text,
                "char_count": len(text),
                "word_count": len(text.split()) if text else 0,
                "page_count": count,
                "status": "error" if not text else "partial",
                "error_message": error_msg
            }

        return {
            "filename": resolved_name,
            "text": text,
            "char_count": len(text),
            "word_count": len(text.split()),
            "page_count": count,
            "status": "success",
            "error_message": None
        }

    @staticmethod
    def extract_candidate_name(text: Optional[str] = None, filename: Optional[str] = None) -> str:
        """Extract or infer candidate display name deterministically from text header or filename.
        
        Args:
            text: Raw extracted resume text.
            filename: Fallback filename string.
            
        Returns:
            Clean candidate display name string.
        """
        # 1. Attempt to derive from the top lines of text
        if text and text.strip():
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            header_ignore = {
                "resume", "curriculum vitae", "cv", "summary", "profile", 
                "professional summary", "contact", "experience", "education", 
                "skills", "technical skills", "work experience"
            }
            
            for line in lines[:6]:
                # Exclude lines containing contact details or long descriptions
                if "@" in line or "http" in line or "www." in line or "linkedin" in line or "github" in line:
                    continue
                if re.search(r'\d{3}[-.\s]?\d{3}', line) or len(line) > 50:
                    continue
                if line.lower() in header_ignore:
                    continue
                
                # Check for standard 2-4 word name pattern
                words = [w for w in re.split(r'\s+', line) if w]
                if 2 <= len(words) <= 4:
                    # Verify each word looks like a name component (alphabetic, titlecase or uppercase)
                    if all(re.match(r"^[A-Z][a-zA-Z\.\'-]*$", w) or w.isupper() for w in words):
                        candidate_name = " ".join(w.capitalize() if w.isupper() else w for w in words)
                        return candidate_name

        # 2. Fallback to filename (sanitized from path traversal)
        if filename:
            clean_name = Path(filename).name.rsplit(".", 1)[0]
            # Strip common suffixes
            clean_name = re.sub(r'[\-_]?(?:resume|cv|profile|v\d+|\d{4})', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'[\-_]+', ' ', clean_name).strip()
            if len(clean_name) >= 3:
                return clean_name.title()

        return "Candidate"
