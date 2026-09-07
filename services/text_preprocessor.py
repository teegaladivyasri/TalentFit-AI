"""NLP Text Preprocessing Service.

Cleans, normalizes, tokenizes, and segments resume and Job Description text
while rigorously preserving technical terms, symbols, and original source text.
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional, Set


# Standard English stopwords, carefully filtered to PROTECT programming languages,
# technical acronyms, and single/two-letter technical words (e.g., 'c', 'r', 'go', 'ai', 'ml', 'it', 'db', 'ui', 'ux', 'os').
SAFE_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}

# Explicit whitelist of words that must NEVER be filtered as stopwords
PROTECTED_TECH_WORDS: Set[str] = {
    "c", "r", "go", "ai", "ml", "it", "db", "ui", "ux", "os", "ip", "qa", "bi", "ci", "cd"
}


# Resume & Job Description standard section header regex patterns
SECTION_PATTERNS = {
    "summary": re.compile(
        r"^(?:professional\s+summary|executive\s+summary|summary|profile|about\s+me|career\s+objective|objective|about\s+the\s+role|role\s+summary)\b", 
        re.IGNORECASE
    ),
    "skills": re.compile(
        r"^(?:technical\s+skills|technical\s+expertise|technical\s+proficiencies|technical\s+background|skills\s*(?:&|and)\s*technologies|skills|core\s+competencies|technologies|tech\s+stack|tools\s*(?:&|and)\s*technologies|key\s+skills)\b", 
        re.IGNORECASE
    ),
    "experience": re.compile(
        r"^(?:work\s+experience|professional\s+experience|professional\s+background|work\s+background|professional\s+history|experience|employment\s+history|work\s+history|career\s+history)\b", 
        re.IGNORECASE
    ),
    "education": re.compile(
        r"^(?:education|academic\s+background|degrees|academic\s+history|education\s*(?:&|and)\s*certifications)\b", 
        re.IGNORECASE
    ),
    "projects": re.compile(
        r"^(?:technical\s+projects|projects|key\s+projects|personal\s+projects|selected\s+projects|selected\s+work|featured\s+projects|notable\s+projects|portfolio)\b", 
        re.IGNORECASE
    ),
    "certifications": re.compile(
        r"^(?:certifications|licenses\s*(?:&|and)\s*certifications|credentials|certificates)\b", 
        re.IGNORECASE
    ),
    "responsibilities": re.compile(
        r"^(?:key\s+responsibilities|responsibilities|what\s+you(?:'ll|\s+will)\s+do|duties|core\s+responsibilities)\b", 
        re.IGNORECASE
    ),
    "requirements": re.compile(
        r"^(?:requirements\s*(?:&|and)\s*qualifications|requirements|qualifications|what\s+we(?:'re|\s+are)\s+looking\s+for|minimum\s+qualifications|basic\s+qualifications|who\s+you\s+are)\b", 
        re.IGNORECASE
    ),
    "preferred_qualifications": re.compile(
        r"^(?:preferred\s+qualifications|nice\s+to\s+have|bonus\s+points|bonus\s+qualifications|desired\s+skills)\b", 
        re.IGNORECASE
    ),
    "benefits": re.compile(
        r"^(?:benefits\s*(?:&|and)\s*perks|benefits|what\s+we\s+offer|compensation)\b", 
        re.IGNORECASE
    )
}


MAX_TEXT_INPUT_LENGTH = 500_000


class TextPreprocessor:
    """Production NLP text preprocessing engine for resumes and job postings."""

    def __init__(self, stopwords: Optional[Set[str]] = None):
        self.stopwords = (stopwords if stopwords is not None else SAFE_STOPWORDS) - PROTECTED_TECH_WORDS

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Apply Unicode NFKC normalization and replace typographic symbols."""
        if not text:
            return ""
        
        # Guard against unbounded text input size
        if len(text) > MAX_TEXT_INPUT_LENGTH:
            text = text[:MAX_TEXT_INPUT_LENGTH]
        
        # Standard NFKC decomposition & recomposition
        normalized = unicodedata.normalize("NFKC", text)
        
        # Replace stylized quotes, bullets, and dashes
        replacements = {
            "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
            "\u2013": "-", "\u2014": "-", "\u2026": "...",
            "\u2022": "\n", "\u25aa": "\n", "\u25ba": "\n", "\u2714": " ",
            "\u2713": " ", "\u2605": " ", "\u00a0": " "
        }
        for orig, repl in replacements.items():
            normalized = normalized.replace(orig, repl)
            
        return normalized

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize line breaks, remove null bytes and control characters, collapse spaces."""
        if not text:
            return ""
            
        # Strip null bytes and non-printable control codes
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        
        # Normalize newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Normalize spaces & tabs on each line
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        
        # Collapse excessive blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        return cleaned.strip()

    def clean_text(
        self, 
        text: str, 
        preserve_case: bool = False, 
        remove_urls_emails: bool = True
    ) -> str:
        """Clean text while rigorously protecting technical terms, punctuation, and version numbers.
        
        Args:
            text: Input raw string.
            preserve_case: Whether to retain original character casing.
            remove_urls_emails: Whether to strip web URLs and email addresses.
            
        Returns:
            Sanitized, normalized string ready for matching and tokenization.
        """
        if not text:
            return ""

        # 1. Unicode & whitespace normalization
        text = self.normalize_unicode(text)
        text = self.normalize_whitespace(text)

        # 2. Remove URLs and Emails if requested
        if remove_urls_emails:
            text = re.sub(r"https?://\S+|www\.\S+", " ", text)
            text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", " ", text)

        # 3. Clean special punctuation characters but preserve technical symbols (+, #, ., -, /, _)
        # Replace non-tech symbols with spaces
        text = re.sub(r"[^\w\s\+\#\.\-\/\_]", " ", text)

        # 4. Collapse repeated spaces
        text = re.sub(r"[ \t]+", " ", text)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        cleaned = "\n".join(lines)

        return cleaned if preserve_case else cleaned.lower()

    def tokenize(
        self, 
        text: str, 
        remove_stopwords: bool = False, 
        min_len: int = 1
    ) -> List[str]:
        """Extract tokens preserving complex technical terms, compound names, and versions.
        
        Examples preserved:
            'C++', 'C#', '.NET', 'Node.js', 'React.js', 'Next.js', 'FastAPI', 
            'CI/CD', 'scikit-learn', '5+ years', 'Python/Django', 'OAuth2.0'
        """
        if not text:
            return []

        cleaned = self.clean_text(text, preserve_case=False)
        
        # Comprehensive regex capturing:
        # 1. Slash-compound terms (e.g., Python/Django, CI/CD, TCP/IP)
        # 2. Dot-prefixed tech (.NET)
        # 3. C++ / C#
        # 4. Dotted tech words (Node.js, Vue.js, v1.0)
        # 5. Hyphenated tech words (scikit-learn, full-stack)
        # 6. Plus-quantifiers (5+, 3+)
        # 7. Standard alphanumeric words
        token_pattern = re.compile(
            r'(?:'
            r'[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+|'   # Slash terms (CI/CD, Python/FastAPI)
            r'\.net\b|'                                 # .NET
            r'\bc\+\+|'                                 # C++
            r'\bc\#|'                                   # C#
            r'[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)+|'         # Dotted terms (Node.js, React.js)
            r'[a-zA-Z0-9]+(?:[\-_][a-zA-Z0-9]+)+|'     # Hyphenated terms (scikit-learn)
            r'[0-9]+\+|'                                # 5+, 10+
            r'[a-zA-Z0-9]+'                             # Standard words/numbers
            r')',
            re.IGNORECASE
        )

        raw_tokens = token_pattern.findall(cleaned)
        
        tokens = []
        for t in raw_tokens:
            tok = t.strip(".-_ ")
            # Restore .net if stripped
            if t.lower() == ".net":
                tok = ".net"
            if len(tok) >= min_len:
                tokens.append(tok)

        if remove_stopwords:
            tokens = self.remove_stopwords(tokens)

        return tokens

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Filter standard English stopwords while protecting domain keywords."""
        if not tokens:
            return []
        return [
            t for t in tokens 
            if (t.lower() not in self.stopwords or t.lower() in PROTECTED_TECH_WORDS)
        ]

    def extract_sections(self, text: str, doc_type: str = "general") -> Dict[str, str]:
        """Partition document text into recognizable semantic sections.
        
        Recognizes standard resume and Job Description headers.
        """
        if not text:
            return {}

        normalized = self.normalize_whitespace(self.normalize_unicode(text))
        lines = normalized.split("\n")
        
        sections: Dict[str, List[str]] = {}
        current_section = "header"
        sections[current_section] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check if line matches a known section header (usually short, <= 45 chars)
            matched_sec = None
            if len(line_str) <= 45:
                # Strip trailing colons or dashes
                header_candidate = re.sub(r"[:\-\–]+$", "", line_str).strip()
                for sec_name, pattern in SECTION_PATTERNS.items():
                    if pattern.match(header_candidate):
                        matched_sec = sec_name
                        break

            if matched_sec:
                current_section = matched_sec
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line_str)

        # Collapse section lines into formatted text blocks
        result_sections: Dict[str, str] = {}
        for sec_name, sec_lines in sections.items():
            sec_text = "\n".join(sec_lines).strip()
            if sec_text:
                result_sections[sec_name] = sec_text

        return result_sections

    def preprocess(
        self, 
        text: str, 
        doc_type: str = "general", 
        remove_stopwords: bool = False
    ) -> Dict[str, Any]:
        """Execute full NLP preprocessing pipeline returning structured representations."""
        if not text or not text.strip():
            return {
                "original_text": text or "",
                "normalized_text": "",
                "cleaned_text": "",
                "tokens": [],
                "token_count": 0,
                "filtered_tokens": [],
                "sections": {},
                "char_count": 0,
                "word_count": 0
            }

        norm_text = self.normalize_whitespace(self.normalize_unicode(text))
        cleaned = self.clean_text(norm_text, preserve_case=False)
        tokens = self.tokenize(norm_text, remove_stopwords=False)
        filtered_tokens = self.remove_stopwords(tokens) if remove_stopwords else []
        sections = self.extract_sections(norm_text, doc_type=doc_type)

        return {
            "original_text": text,
            "normalized_text": norm_text,
            "cleaned_text": cleaned,
            "tokens": tokens,
            "token_count": len(tokens),
            "filtered_tokens": filtered_tokens if remove_stopwords else self.remove_stopwords(tokens),
            "sections": sections,
            "char_count": len(norm_text),
            "word_count": len(tokens)
        }
