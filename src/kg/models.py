# c:\Users\ncvet\cdr-platform\src\kg\models.py
"""
Data models for the waste knowledge graph.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple
from datetime import date


class WasteEntryType(str, Enum):
    """Classification of waste entry types from LoW."""
    ABSOLUTE_HAZARDOUS = "AH"      # Always hazardous
    MIRROR_HAZARDOUS = "MH"        # Hazardous if contains dangerous substances above threshold
    MIRROR_NON_HAZARDOUS = "MNH"   # Non-hazardous mirror entry
    ABSOLUTE_NON_HAZARDOUS = "ANH" # Never hazardous


class HazardousPropertyCode(str, Enum):
    """HP codes as defined in Annex III of the Waste Framework Directive."""
    HP1 = "HP1"   # Explosive
    HP2 = "HP2"   # Oxidising
    HP3 = "HP3"   # Flammable
    HP4 = "HP4"   # Irritant
    HP5 = "HP5"   # Specific Target Organ Toxicity / Aspiration Toxicity
    HP6 = "HP6"   # Acute Toxicity
    HP7 = "HP7"   # Carcinogenic
    HP8 = "HP8"   # Corrosive
    HP9 = "HP9"   # Infectious
    HP10 = "HP10" # Toxic for Reproduction
    HP11 = "HP11" # Mutagenic
    HP12 = "HP12" # Release of Acute Toxic Gas
    HP13 = "HP13" # Sensitising
    HP14 = "HP14" # Ecotoxic
    HP15 = "HP15" # Capable of Exhibiting Hazardous Property


@dataclass
class HazardousProperty:
    """Represents an HP classification."""
    code: str
    label: str
    description: Optional[str] = None
    
    def __hash__(self):
        return hash(self.code)
    
    def __eq__(self, other):
        if isinstance(other, HazardousProperty):
            return self.code == other.code
        return False


@dataclass
class ConcentrationThreshold:
    """Threshold concentration for HP classification."""
    hp_code: str
    hazard_statement: str
    threshold_percent: float
    threshold_type: str = "single"  # "single" or "sum"
    notes: Optional[str] = None


@dataclass
class Substance:
    """A chemical substance that may be present in waste."""
    name: str
    cas_number: Optional[str] = None
    ec_number: Optional[str] = None
    chebi_id: Optional[str] = None
    hazard_statements: List[str] = field(default_factory=list)


@dataclass
class WasteEntry:
    """Represents a waste entry from the List of Waste."""
    low_code: str
    description: str
    entry_type: WasteEntryType
    hp_properties: Set[str] = field(default_factory=set)
    chapter: Optional[str] = None
    subchapter: Optional[str] = None
    is_hazardous: bool = False
    substances: List[Substance] = field(default_factory=list)
    
    def __post_init__(self):
        # Entries with * are hazardous
        self.is_hazardous = self.low_code.endswith("*") or self.entry_type in [
            WasteEntryType.ABSOLUTE_HAZARDOUS,
            WasteEntryType.MIRROR_HAZARDOUS
        ]
    
    @property
    def normalized_code(self) -> str:
        """Return code without asterisk for comparison."""
        return self.low_code.rstrip("*").strip()
    
    def __hash__(self):
        return hash(self.low_code)
    
    def __eq__(self, other):
        if isinstance(other, WasteEntry):
            return self.low_code == other.low_code
        return False


@dataclass
class IncompatibilityConflict:
    """Represents a specific incompatibility between two HP properties."""
    hp_a: str
    hp_b: str
    reason: str
    severity: str = "HIGH"  # HIGH, MEDIUM, LOW


@dataclass
class CompatibilityResult:
    """Result of a waste compatibility check."""
    compatible: bool
    waste_a: str
    waste_b: str
    conflicts: List[IncompatibilityConflict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)
    
    def add_conflict(self, hp_a: str, hp_b: str, reason: str, severity: str = "HIGH"):
        self.conflicts.append(IncompatibilityConflict(hp_a, hp_b, reason, severity))
        self.compatible = False
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def add_recommendation(self, recommendation: str):
        self.recommendations.append(recommendation)


@dataclass
class CLPHazardStatement:
    """CLP hazard statement code and associated information."""
    code: str
    description: str
    hazard_class: str
    category: Optional[str] = None
    triggers_hp: List[str] = field(default_factory=list)


@dataclass
class RegulatoryContext:
    """Temporal context for regulatory validity."""
    regulation_name: str
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    jurisdiction: str = "EU"
    notes: Optional[str] = None