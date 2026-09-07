"""Comprehensive unit tests for the DocumentParser service."""

import io
import pytest
import docx
import pypdf
from services.document_parser import DocumentParser


class MockUploadedFile:
    """Mock simulating Streamlit's UploadedFile object."""
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data
        self.size = len(data)

    def getvalue(self) -> bytes:
        return self._data

    def read(self) -> bytes:
        return self._data


def create_sample_pdf_bytes(text: str = "Candidate Name: Jane Doe\nSkills: Python, React, SQL") -> bytes:
    """Generate in-memory valid PDF bytes using pypdf writer."""
    # Create a minimal PDF with page and text using pypdf
    writer = pypdf.PdfWriter()
    # Add a blank page
    page = writer.add_blank_page(width=612, height=792)
    
    # We can write text or annotations, or create a simple standard stream
    # pypdf doesn't draw text easily without reportlab, but we can write raw PDF objects
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def create_sample_pdf_with_text(text: str) -> bytes:
    """Create a valid PDF containing text streams in-memory."""
    # Standard raw minimal PDF format with Helvetica font and BT/ET text stream
    pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(text) + 50} >>
stream
BT
/F1 12 Tf
72 700 Td
({text}) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000350 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
425
%%EOF"""
    return pdf_content.encode("latin-1")


def create_sample_docx_bytes(paragraphs=None, table_data=None) -> bytes:
    """Generate in-memory valid DOCX bytes using python-docx."""
    doc = docx.Document()
    if paragraphs:
        for p in paragraphs:
            doc.add_paragraph(p)
    if table_data:
        table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
        for r_idx, row in enumerate(table_data):
            for c_idx, val in enumerate(row):
                table.cell(r_idx, c_idx).text = str(val)
                
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def parser():
    return DocumentParser()


# ---------------------------------------------------------------------------
# PDF Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_text_from_valid_pdf(parser):
    pdf_bytes = create_sample_pdf_with_text("Jane Doe Senior Software Engineer Python React")
    text, pages, err = parser.extract_text_from_pdf(pdf_bytes)
    assert err is None
    assert "Jane Doe" in text
    assert "Python" in text
    assert pages >= 1


def test_extract_text_from_empty_pdf_bytes(parser):
    text, pages, err = parser.extract_text_from_pdf(b"")
    assert text == ""
    assert pages == 0
    assert "empty" in err.lower()


def test_extract_text_from_corrupted_pdf(parser):
    corrupted_bytes = b"%PDF-1.4 corrupted invalid stream data 12345"
    text, pages, err = parser.extract_text_from_pdf(corrupted_bytes)
    assert text == ""
    assert err is not None
    assert "unable to parse" in err.lower() or "pdf" in err.lower()


# ---------------------------------------------------------------------------
# DOCX Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_text_from_valid_docx(parser):
    paragraphs = [
        "Alex Morgan - Full Stack Engineer",
        "Experience: 5 years in backend Python microservices and React.",
        "Education: BS in Computer Science"
    ]
    table_data = [
        ["Skill Category", "Proficiency"],
        ["Languages", "Python, TypeScript, SQL"],
        ["DevOps", "Docker, Kubernetes, AWS"]
    ]
    docx_bytes = create_sample_docx_bytes(paragraphs, table_data)
    text, count, err = parser.extract_text_from_docx(docx_bytes)
    
    assert err is None
    assert "Alex Morgan" in text
    assert "Python microservices" in text
    assert "Docker, Kubernetes, AWS" in text


def test_extract_text_from_empty_docx_bytes(parser):
    text, count, err = parser.extract_text_from_docx(b"")
    assert text == ""
    assert err is not None
    assert "empty" in err.lower()


def test_extract_text_from_corrupted_docx(parser):
    corrupted = b"PK\x03\x04 corrupt zip archive not a real docx"
    text, count, err = parser.extract_text_from_docx(corrupted)
    assert text == ""
    assert err is not None
    assert "unable to parse" in err.lower()


def test_extract_text_from_blank_docx_document(parser):
    # DOCX file that exists but has no text content
    blank_docx_bytes = create_sample_docx_bytes([])
    text, count, err = parser.extract_text_from_docx(blank_docx_bytes)
    assert text == ""
    assert err is not None
    assert "no readable text" in err.lower()


# ---------------------------------------------------------------------------
# TXT Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_text_from_utf8_txt(parser):
    txt_content = "Job Title: Senior Backend Developer\nRequirements:\n- Python 3.11\n- PostgreSQL\n- FastAPI"
    text, lines, err = parser.extract_text_from_txt(txt_content.encode("utf-8"))
    assert err is None
    assert "Senior Backend Developer" in text
    assert "FastAPI" in text


def test_extract_text_from_latin1_txt(parser):
    txt_content = "Rôle: Développeur Full Stack Senior (Montréal, Québec)"
    text, lines, err = parser.extract_text_from_txt(txt_content.encode("latin-1"))
    assert err is None
    assert "Développeur" in text or "Full Stack" in text


def test_extract_text_from_empty_txt(parser):
    text, lines, err = parser.extract_text_from_txt(b"")
    assert text == ""
    assert err is not None
    assert "empty" in err.lower()


def test_extract_text_from_string_input(parser):
    text, lines, err = parser.extract_text_from_txt("Direct string job description.")
    assert err is None
    assert text == "Direct string job description."


# ---------------------------------------------------------------------------
# Sanitization and Normalization Tests
# ---------------------------------------------------------------------------

def test_sanitize_text_null_bytes_and_spaces():
    raw = "Hello\x00 World!\r\n\r\nThis   has   extra    spaces.\n\n\n\nToo many newlines."
    cleaned = DocumentParser._sanitize_text(raw)
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "This has extra spaces." in cleaned
    assert "\n\n\n" not in cleaned


# ---------------------------------------------------------------------------
# Unified parse_document Dispatcher Tests
# ---------------------------------------------------------------------------

def test_parse_document_with_mock_uploaded_pdf(parser):
    pdf_bytes = create_sample_pdf_with_text("Jordan Taylor Resume\nPython React AWS Docker")
    mock_file = MockUploadedFile("jordan_taylor_resume.pdf", pdf_bytes)
    
    result = parser.parse_document(mock_file)
    assert result["status"] == "success"
    assert result["filename"] == "jordan_taylor_resume.pdf"
    assert "Jordan Taylor" in result["text"]
    assert result["word_count"] > 0
    assert result["char_count"] > 0
    assert result["page_count"] >= 1
    assert result["error_message"] is None


def test_parse_document_with_mock_uploaded_docx(parser):
    docx_bytes = create_sample_docx_bytes(["Software Engineer Resume Content", "Skills: Python, SQL"])
    mock_file = MockUploadedFile("candidate.docx", docx_bytes)
    
    result = parser.parse_document(mock_file)
    assert result["status"] == "success"
    assert result["filename"] == "candidate.docx"
    assert "Software Engineer" in result["text"]
    assert result["error_message"] is None


def test_parse_document_unsupported_format(parser):
    mock_file = MockUploadedFile("photo.png", b"\x89PNG\r\n\x1a\n")
    result = parser.parse_document(mock_file)
    assert result["status"] == "error"
    assert "unsupported" in result["error_message"].lower()


def test_parse_document_none_input(parser):
    result = parser.parse_document(None)
    assert result["status"] == "empty"
    assert result["text"] == ""
