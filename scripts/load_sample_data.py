# c:\Users\ncvet\cdr-platform\scripts\load_sample_data.py
"""
Script to load sample waste data into the knowledge graph.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg.graph_store import WasteKnowledgeGraph
from kg.models import WasteEntry, WasteEntryType


def create_sample_entries() -> list[WasteEntry]:
    """Create sample waste entries for testing."""
    return [
        # Chapter 07 - Wastes from organic chemical processes
        WasteEntry(
            low_code="07 01 03*",
            description="organic halogenated solvents, washing liquids and mother liquors",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3", "HP6", "HP14"},  # Flammable, Acute Toxic, Ecotoxic
            chapter="07",
            subchapter="07 01"
        ),
        WasteEntry(
            low_code="07 01 04*",
            description="other organic solvents, washing liquids and mother liquors",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3", "HP6"},  # Flammable, Acute Toxic
            chapter="07",
            subchapter="07 01"
        ),
        
        # Chapter 11 - Wastes from chemical surface treatment
        WasteEntry(
            low_code="11 01 05*",
            description="pickling acids",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP4", "HP8"},  # Irritant, Corrosive
            chapter="11",
            subchapter="11 01"
        ),
        WasteEntry(
            low_code="11 01 06*",
            description="acids not otherwise specified",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP8"},  # Corrosive
            chapter="11",
            subchapter="11 01"
        ),
        WasteEntry(
            low_code="11 01 07*",
            description="pickling bases",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP8"},  # Corrosive
            chapter="11",
            subchapter="11 01"
        ),
        WasteEntry(
            low_code="11 01 09*",
            description="sludges and filter cakes containing dangerous substances",
            entry_type=WasteEntryType.MIRROR_HAZARDOUS,
            hp_properties={"HP4", "HP6", "HP14"},  # Irritant, Acute Toxic, Ecotoxic
            chapter="11",
            subchapter="11 01"
        ),
        WasteEntry(
            low_code="11 01 10",
            description="sludges and filter cakes other than those mentioned in 11 01 09",
            entry_type=WasteEntryType.MIRROR_NON_HAZARDOUS,
            hp_properties=set(),
            chapter="11",
            subchapter="11 01"
        ),
        
        # Chapter 13 - Oil wastes
        WasteEntry(
            low_code="13 01 10*",
            description="mineral based non-chlorinated hydraulic oils",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3", "HP14"},  # Flammable, Ecotoxic
            chapter="13",
            subchapter="13 01"
        ),
        WasteEntry(
            low_code="13 02 05*",
            description="mineral-based non-chlorinated engine, gear and lubricating oils",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3", "HP14"},  # Flammable, Ecotoxic
            chapter="13",
            subchapter="13 02"
        ),
        
        # Chapter 14 - Waste organic solvents
        WasteEntry(
            low_code="14 06 02*",
            description="other halogenated solvents and solvent mixtures",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3", "HP6", "HP7"},  # Flammable, Acute Toxic, Carcinogenic
            chapter="14",
            subchapter="14 06"
        ),
        
        # Chapter 16 - Wastes not otherwise specified
        WasteEntry(
            low_code="16 05 06*",
            description="laboratory chemicals, consisting of or containing dangerous substances, including mixtures of laboratory chemicals",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3", "HP6", "HP8", "HP14"},  # Multiple hazards
            chapter="16",
            subchapter="16 05"
        ),
        WasteEntry(
            low_code="16 05 07*",
            description="discarded inorganic chemicals consisting of or containing dangerous substances",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP2", "HP8"},  # Oxidising, Corrosive
            chapter="16",
            subchapter="16 05"
        ),
        WasteEntry(
            low_code="16 05 08*",
            description="discarded organic chemicals consisting of or containing dangerous substances",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP3", "HP6"},  # Flammable, Acute Toxic
            chapter="16",
            subchapter="16 05"
        ),
        
        # Chapter 18 - Healthcare wastes
        WasteEntry(
            low_code="18 01 03*",
            description="wastes whose collection and disposal is subject to special requirements in order to prevent infection",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP9"},  # Infectious
            chapter="18",
            subchapter="18 01"
        ),
        
        # Chapter 06 - Wastes from inorganic chemical processes
        WasteEntry(
            low_code="06 01 01*",
            description="sulphuric acid and sulphurous acid",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP8"},  # Corrosive
            chapter="06",
            subchapter="06 01"
        ),
        WasteEntry(
            low_code="06 01 02*",
            description="hydrochloric acid",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP8"},  # Corrosive
            chapter="06",
            subchapter="06 01"
        ),
        WasteEntry(
            low_code="06 03 11*",
            description="solid salts and solutions containing cyanides",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP6", "HP12"},  # Acute Toxic, Release of toxic gas
            chapter="06",
            subchapter="06 03"
        ),
        
        # Explosive waste example
        WasteEntry(
            low_code="16 04 01*",
            description="waste ammunition",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP1"},  # Explosive
            chapter="16",
            subchapter="16 04"
        ),
        
        # Oxidising waste example
        WasteEntry(
            low_code="16 09 01*",
            description="permanganates, for example potassium permanganate",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP2", "HP14"},  # Oxidising, Ecotoxic
            chapter="16",
            subchapter="16 09"
        ),
        WasteEntry(
            low_code="16 09 02*",
            description="chromates, for example potassium chromate, potassium or sodium dichromate",
            entry_type=WasteEntryType.ABSOLUTE_HAZARDOUS,
            hp_properties={"HP2", "HP7", "HP14"},  # Oxidising, Carcinogenic, Ecotoxic
            chapter="16",
            subchapter="16 09"
        ),
    ]


def main():
    """Load sample data into the knowledge graph."""
    # Initialize KG with ontology
    ontology_path = Path(__file__).parent.parent / "ontology" / "waste-hp.ttl"
    kg = WasteKnowledgeGraph(ontology_path if ontology_path.exists() else None)
    
    # Create and add sample entries
    entries = create_sample_entries()
    for entry in entries:
        kg.add_waste_entry(entry)
        print(f"Added: {entry.low_code} - {entry.description[:50]}...")
    
    # Save the graph
    output_path = Path(__file__).parent.parent / "data" / "waste_kg.ttl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    kg.save(output_path)
    
    print(f"\nSaved knowledge graph to {output_path}")
    print(f"Statistics: {kg.get_statistics()}")
    
    # Test compatibility check
    print("\n--- Testing Compatibility Checks ---")
    
    # Test 1: Flammable + Oxidising (should be incompatible)
    result = kg.check_compatibility("07 01 03*", "16 09 01*")
    print(f"\n{result.waste_a} + {result.waste_b}:")
    print(f"  Compatible: {result.compatible}")
    for conflict in result.conflicts:
        print(f"  Conflict: {conflict.hp_a} vs {conflict.hp_b} ({conflict.severity})")
        print(f"    Reason: {conflict.reason}")
    
    # Test 2: Corrosive + Toxic gas release (should be incompatible)
    result = kg.check_compatibility("06 01 01*", "06 03 11*")
    print(f"\n{result.waste_a} + {result.waste_b}:")
    print(f"  Compatible: {result.compatible}")
    for conflict in result.conflicts:
        print(f"  Conflict: {conflict.hp_a} vs {conflict.hp_b} ({conflict.severity})")
        print(f"    Reason: {conflict.reason}")
    
    # Test 3: Infectious + Non-infectious (should have warning)
    result = kg.check_compatibility("18 01 03*", "07 01 03*")
    print(f"\n{result.waste_a} + {result.waste_b}:")
    print(f"  Compatible: {result.compatible}")
    for conflict in result.conflicts:
        print(f"  Conflict: {conflict.hp_a} vs {conflict.hp_b}")
    for warning in result.warnings:
        print(f"  Warning: {warning}")


if __name__ == "__main__":
    main()