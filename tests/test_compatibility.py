# c:\Users\ncvet\cdr-platform\tests\test_compatibility.py
"""
Tests for waste compatibility checking.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg.graph_store import WasteKnowledgeGraph
from kg.models import WasteEntry, WasteEntryType
from kg.incompatibility_rules import (
    are_hp_incompatible,
    get_incompatibility_reason,
    get_severity,
)


class TestIncompatibilityRules:
    """Test the HP incompatibility rules."""
    
    def test_hp2_hp3_incompatible(self):
        """Oxidising and Flammable should be incompatible."""
        assert are_hp_incompatible("HP2", "HP3")
        assert are_hp_incompatible("HP3", "HP2")  # Symmetric
    
    def test_hp2_hp3_reason(self):
        """Should provide a reason for incompatibility."""
        reason = get_incompatibility_reason("HP2", "HP3")
        assert reason is not None
        assert "fire" in reason.lower() or "explosion" in reason.lower()
    
    def test_compatible_hps(self):
        """Some HP combinations should be compatible."""
        # HP7 (Carcinogenic) and HP4 (Irritant) are not in incompatibility rules
        assert not are_hp_incompatible("HP7", "HP4")
    
    def test_severity_levels(self):
        """Test severity classification."""
        # Explosive + Oxidising should be critical
        assert get_severity("HP1", "HP2") in ["CRITICAL", "HIGH"]
        
        # Corrosive + Toxic gas release should be critical
        assert get_severity("HP8", "HP12") in ["CRITICAL", "HIGH"]


class TestKnowledgeGraph:
    """Test the knowledge graph operations."""
    
    @pytest.fixture
    def kg(self):
        """Create a knowledge graph with test data."""
        kg = WasteKnowledgeGraph()
        
        # Add test entries
        kg.add_waste_entry(WasteEntry(
            low_code="TEST-001*",
            description="Test flammable waste",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3"}
        ))
        
        kg.add_waste_entry(WasteEntry(
            low_code="TEST-002*",
            description="Test oxidising waste",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP2"}
        ))
        
        kg.add_waste_entry(WasteEntry(
            low_code="TEST-003",
            description="Test non-hazardous waste",
            entry_type=WasteEntryType.ABSOLUTE_NON_HAZARDOUS,
            hp_properties=set()
        ))
        
        return kg
    
    def test_add_and_retrieve_waste(self, kg):
        """Test adding and retrieving waste entries."""
        entry = kg.get_waste_entry("TEST-001*")
        assert entry is not None
        assert entry.low_code == "TEST-001*"
        assert "HP3" in entry.hp_properties
    
    def test_compatibility_check_incompatible(self, kg):
        """Test compatibility check for incompatible wastes."""
        result = kg.check_compatibility("TEST-001*", "TEST-002*")
        assert not result.compatible
        assert len(result.conflicts) > 0
    
    def test_compatibility_check_compatible(self, kg):
        """Test compatibility check for compatible wastes."""
        # Non-hazardous waste should be compatible with anything
        result = kg.check_compatibility("TEST-001*", "TEST-003")
        # Should be compatible (no HP conflicts)
        assert result.compatible or len(result.conflicts) == 0
    
    def test_get_wastes_with_hp(self, kg):
        """Test filtering wastes by HP property."""
        flammable_wastes = kg.get_wastes_with_hp("HP3")
        assert len(flammable_wastes) >= 1
        assert any(w.low_code == "TEST-001*" for w in flammable_wastes)


class TestCompatibilityResult:
    """Test the CompatibilityResult model."""
    
    def test_add_conflict(self):
        """Test adding conflicts to result."""
        from kg.models import CompatibilityResult
        
        result = CompatibilityResult(
            compatible=True,
            waste_a="A",
            waste_b="B"
        )
        
        assert result.compatible
        
        result.add_conflict("HP2", "HP3", "Test reason", "HIGH")
        
        assert not result.compatible
        assert result.conflict_count == 1
    
    def test_warnings_and_recommendations(self):
        """Test adding warnings and recommendations."""
        from kg.models import CompatibilityResult
        
        result = CompatibilityResult(
            compatible=True,
            waste_a="A",
            waste_b="B"
        )
        
        result.add_warning("Test warning")
        result.add_recommendation("Test recommendation")
        
        assert "Test warning" in result.warnings
        assert "Test recommendation" in result.recommendations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])