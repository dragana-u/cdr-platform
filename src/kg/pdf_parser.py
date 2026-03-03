# c:\Users\ncvet\cdr-platform\src\kg\pdf_parser.py
"""
PDF parsing utilities for extracting List of Waste (LoW) entries.
Uses pdfplumber for text extraction and rule-based parsing for structured tables.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Generator
from dataclasses import dataclass

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from .models import WasteEntry, WasteEntryType

logger = logging.getLogger(__name__)


@dataclass
class ParsedRow:
    """A parsed row from the LoW table."""
    code: str
    description: str
    is_hazardous: bool
    raw_text: str


class LoWPDFParser:
    """
    Parser for EU List of Waste PDF documents.
    
    Extracts waste codes, descriptions, and determines entry types
    (AH, MH, MNH, ANH) based on document structure.
    """
    
    # Regex patterns for LoW codes
    # Format: XX XX XX or XX XX XX* (with asterisk for hazardous)
    LOW_CODE_PATTERN = re.compile(
        r'^(\d{2})\s+(\d{2})\s+(\d{2})(\*)?$'
    )
    
    # Chapter pattern (XX)
    CHAPTER_PATTERN = re.compile(r'^(\d{2})\s+(.+)$')
    
    # Subchapter pattern (XX XX)
    SUBCHAPTER_PATTERN = re.compile(r'^(\d{2})\s+(\d{2})\s+(.+)$')
    
    def __init__(self):
        if pdfplumber is None:
            raise ImportError(
                "pdfplumber is required for PDF parsing. "
                "Install with: pip install pdfplumber"
            )
        self.current_chapter: Optional[str] = None
        self.current_subchapter: Optional[str] = None
        self.mirror_entry_pairs: Dict[str, str] = {}  # hazardous -> non-hazardous
    
    def parse_pdf(self, pdf_path: Path) -> List[WasteEntry]:
        """
        Parse a LoW PDF and extract all waste entries.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of WasteEntry objects
        """
        entries = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                logger.debug(f"Processing page {page_num}")
                
                # Try table extraction first
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        entries.extend(self._parse_table(table))
                else:
                    # Fall back to text extraction
                    text = page.extract_text()
                    if text:
                        entries.extend(self._parse_text(text))
        
        # Post-process to identify mirror entries
        entries = self._identify_mirror_entries(entries)
        
        logger.info(f"Parsed {len(entries)} waste entries from {pdf_path}")
        return entries
    
    def _parse_table(self, table: List[List[str]]) -> List[WasteEntry]:
        """Parse a table extracted from PDF."""
        entries = []
        
        for row in table:
            if not row or all(cell is None or cell.strip() == '' for cell in row):
                continue
            
            # Try to extract code and description
            entry = self._parse_row(row)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_row(self, row: List[str]) -> Optional[WasteEntry]:
        """Parse a single table row."""
        # Clean and join cells
        cells = [str(c).strip() if c else '' for c in row]
        
        # Look for LoW code pattern in first cell(s)
        code_match = None
        description = ""
        
        for i, cell in enumerate(cells):
            code_match = self.LOW_CODE_PATTERN.match(cell)
            if code_match:
                # Rest of cells form description
                description = ' '.join(cells[i+1:]).strip()
                break
        
        if not code_match:
            # Check if first cell might be chapter/subchapter
            self._check_chapter_subchapter(cells[0] if cells else "")
            return None
        
        # Construct the code
        parts = code_match.groups()
        code = f"{parts[0]} {parts[1]} {parts[2]}"
        is_hazardous = parts[3] == '*'
        
        if is_hazardous:
            code += '*'
        
        # Determine entry type (will be refined in post-processing)
        entry_type = (
            WasteEntryType.ABSOLUTE_HAZARDOUS if is_hazardous 
            else WasteEntryType.ABSOLUTE_NON_HAZARDOUS
        )
        
        return WasteEntry(
            low_code=code,
            description=description or "No description",
            entry_type=entry_type,
            chapter=self.current_chapter,
            subchapter=self.current_subchapter
        )
    
    def _parse_text(self, text: str) -> List[WasteEntry]:
        """Parse text content when tables aren't available."""
        entries = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for chapter/subchapter
            self._check_chapter_subchapter(line)
            
            # Look for LoW code at start of line
            code_match = self.LOW_CODE_PATTERN.match(line.split()[0] if line.split() else "")
            
            # Alternative: look for pattern anywhere in line
            if not code_match:
                match = re.search(r'(\d{2})\s+(\d{2})\s+(\d{2})(\*)?', line)
                if match:
                    parts = match.groups()
                    code = f"{parts[0]} {parts[1]} {parts[2]}"
                    is_hazardous = parts[3] == '*'
                    if is_hazardous:
                        code += '*'
                    
                    # Extract description (text after the code)
                    desc_start = match.end()
                    description = line[desc_start:].strip()
                    
                    entry_type = (
                        WasteEntryType.ABSOLUTE_HAZARDOUS if is_hazardous
                        else WasteEntryType.ABSOLUTE_NON_HAZARDOUS
                    )
                    
                    entries.append(WasteEntry(
                        low_code=code,
                        description=description or "No description",
                        entry_type=entry_type,
                        chapter=self.current_chapter,
                        subchapter=self.current_subchapter
                    ))
        
        return entries
    
    def _check_chapter_subchapter(self, text: str):
        """Check if text represents a chapter or subchapter header."""
        text = text.strip()
        
        # Check for subchapter first (more specific)
        sub_match = self.SUBCHAPTER_PATTERN.match(text)
        if sub_match:
            self.current_subchapter = f"{sub_match.group(1)} {sub_match.group(2)}"
            return
        
        # Check for chapter
        ch_match = self.CHAPTER_PATTERN.match(text)
        if ch_match and len(ch_match.group(1)) == 2:
            self.current_chapter = ch_match.group(1)
            self.current_subchapter = None
    
    def _identify_mirror_entries(self, entries: List[WasteEntry]) -> List[WasteEntry]:
        """
        Identify and classify mirror entries.
        
        Mirror entries come in pairs:
        - XX XX XX* (Mirror Hazardous) - if dangerous substances present
        - XX XX XX  (Mirror Non-Hazardous) - otherwise
        
        The key indicator is similar descriptions with "containing/not containing
        dangerous substances" or similar phrasing.
        """
        # Group entries by base code (without asterisk)
        code_groups: Dict[str, List[WasteEntry]] = {}
        for entry in entries:
            base_code = entry.low_code.rstrip('*').strip()
            if base_code not in code_groups:
                code_groups[base_code] = []
            code_groups[base_code].append(entry)
        
        # Identify mirror pairs
        for base_code, group in code_groups.items():
            if len(group) == 2:
                # Likely a mirror pair
                hazardous = next((e for e in group if e.is_hazardous), None)
                non_hazardous = next((e for e in group if not e.is_hazardous), None)
                
                if hazardous and non_hazardous:
                    # Check descriptions for mirror indicators
                    if self._is_mirror_pair(hazardous.description, non_hazardous.description):
                        hazardous.entry_type = WasteEntryType.MIRROR_HAZARDOUS
                        non_hazardous.entry_type = WasteEntryType.MIRROR_NON_HAZARDOUS
        
        # Also check for description-based indicators
        mirror_keywords = [
            "containing dangerous substances",
            "containing hazardous substances", 
            "other than those mentioned in",
            "not containing dangerous substances"
        ]
        
        for entry in entries:
            desc_lower = entry.description.lower()
            if any(kw in desc_lower for kw in mirror_keywords):
                if entry.is_hazardous:
                    entry.entry_type = WasteEntryType.MIRROR_HAZARDOUS
                else:
                    entry.entry_type = WasteEntryType.MIRROR_NON_HAZARDOUS
        
        return entries
    
    def _is_mirror_pair(self, desc_hazardous: str, desc_non_hazardous: str) -> bool:
        """Check if two descriptions indicate a mirror pair."""
        indicators = [
            ("containing dangerous", "other than"),
            ("containing hazardous", "other than"),
            ("dangerous substances", "not containing"),
        ]
        
        h_lower = desc_hazardous.lower()
        nh_lower = desc_non_hazardous.lower()
        
        for h_indicator, nh_indicator in indicators:
            if h_indicator in h_lower and nh_indicator in nh_lower:
                return True
        
        return False


class HPThresholdExtractor:
    """
    Extract HP threshold information from technical guidance documents.
    
    This uses a combination of rule-based parsing and can be extended
    with LLM-assisted extraction for complex cases.
    """
    
    # Known HP thresholds from Annex III of WFD (simplified)
    STANDARD_THRESHOLDS = {
        "HP4": {  # Irritant
            "H315": 20.0,  # Skin irritation Cat 2
            "H319": 20.0,  # Eye irritation Cat 2
        },
        "HP5": {  # STOT/Aspiration
            "H370": 1.0,   # STOT SE 1
            "H371": 10.0,  # STOT SE 2
            "H372": 1.0,   # STOT RE 1
            "H373": 10.0,  # STOT RE 2
            "H304": 10.0,  # Aspiration hazard Cat 1
        },
        "HP6": {  # Acute toxicity
            "H300": 0.1,   # Acute Tox 1 Oral
            "H310": 0.25,  # Acute Tox 1 Dermal
            "H330": 0.1,   # Acute Tox 1 Inhalation
            "H301": 5.0,   # Acute Tox 2 Oral
            "H311": 5.0,   # Acute Tox 2 Dermal
            "H331": 2.5,   # Acute Tox 2 Inhalation
        },
        "HP7": {  # Carcinogenic
            "H350": 0.1,   # Carc 1A/1B
            "H351": 1.0,   # Carc 2
        },
        "HP8": {  # Corrosive
            "H314": 5.0,   # Skin Corr 1A/1B/1C
        },
        "HP10": {  # Toxic for reproduction
            "H360": 0.3,   # Repr 1A/1B
            "H361": 3.0,   # Repr 2
        },
        "HP11": {  # Mutagenic
            "H340": 0.1,   # Muta 1A/1B
            "H341": 1.0,   # Muta 2
        },
        "HP14": {  # Ecotoxic (post-2018 rules)
            "H400": 0.1,   # Aquatic Acute 1
            "H410": 0.1,   # Aquatic Chronic 1
            "H411": 1.0,   # Aquatic Chronic 2
            "H412": 10.0,  # Aquatic Chronic 3
            "H413": 25.0,  # Aquatic Chronic 4 (sum rule)
        },
    }
    
    def get_thresholds_for_hp(self, hp_code: str) -> Dict[str, float]:
        """Get threshold concentrations for an HP property."""
        return self.STANDARD_THRESHOLDS.get(hp_code, {})
    
    def check_hp_assignment(
        self, 
        hp_code: str, 
        substance_concentrations: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Check if a waste should be assigned an HP based on substance concentrations.
        
        Args:
            hp_code: HP code to check
            substance_concentrations: Dict mapping H-statement codes to concentration %
        
        Returns:
            Tuple of (should_assign_hp, list_of_triggering_statements)
        """
        thresholds = self.get_thresholds_for_hp(hp_code)
        triggers = []
        
        for h_code, threshold in thresholds.items():
            if h_code in substance_concentrations:
                if substance_concentrations[h_code] >= threshold:
                    triggers.append(h_code)
        
        return len(triggers) > 0, triggers