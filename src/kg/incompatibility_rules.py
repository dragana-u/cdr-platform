# c:\Users\ncvet\cdr-platform\src\kg\incompatibility_rules.py
"""
Domain knowledge: HP-to-HP incompatibility rules.

These rules encode which hazardous properties should not be mixed together,
based on chemical reactivity and safety considerations.
"""

from typing import Dict, FrozenSet, List, Tuple, Optional

# HP incompatibility pairs with reasons
# Format: (HP_A, HP_B) -> reason
_INCOMPATIBLE_HP_RULES: Dict[FrozenSet[str], str] = {
    frozenset({"HP2", "HP3"}): "Oxidiser + Flammable: Risk of fire/explosion. Oxidising agents can cause or intensify combustion of flammable materials.",
    
    frozenset({"HP2", "HP11"}): "Oxidiser + Mutagenic: Oxidising agents may react violently with organic mutagenic compounds, potentially creating hazardous decomposition products.",
    
    frozenset({"HP3", "HP12"}): "Flammable + Toxic Gas Release: Multiple hazard scenario - flammable atmosphere combined with potential toxic gas release creates compounded risk.",
    
    frozenset({"HP4", "HP8"}): "Irritant + Corrosive: Mixing can create concentrated corrosive solutions with enhanced tissue damage potential.",
    
    frozenset({"HP1", "HP2"}): "Explosive + Oxidising: Oxidisers can sensitise explosive materials or lower their initiation threshold.",
    
    frozenset({"HP1", "HP3"}): "Explosive + Flammable: Fire from flammable materials can provide ignition source for explosive waste.",
    
    frozenset({"HP8", "HP12"}): "Corrosive + Toxic Gas Release: Corrosive acids or bases can trigger release of toxic gases (e.g., HCN from cyanides, H2S from sulfides).",
    
    frozenset({"HP1", "HP4"}): "Explosive + Irritant: Some irritant substances may sensitise explosive materials.",
    
    frozenset({"HP2", "HP6"}): "Oxidiser + Acute Toxic: Oxidation may enhance bioavailability or create more toxic oxidation products.",
    
    frozenset({"HP3", "HP6"}): "Flammable + Acute Toxic: Fire scenario with toxic waste creates dual exposure hazard (thermal + toxic).",
    
    frozenset({"HP2", "HP8"}): "Oxidiser + Corrosive: Many corrosive substances are also oxidising (e.g., nitric acid), mixing can cause violent reactions.",
    
    frozenset({"HP6", "HP12"}): "Acute Toxic + Toxic Gas Release: Compounded toxic exposure risk through multiple pathways.",
}

# Convert to the simpler tuple format for backward compatibility
INCOMPATIBLE_HP_PAIRS: Dict[Tuple[str, str], str] = {}
for hp_set, reason in _INCOMPATIBLE_HP_RULES.items():
    hp_list = sorted(list(hp_set))
    # Add both orderings for easy lookup
    INCOMPATIBLE_HP_PAIRS[(hp_list[0], hp_list[1])] = reason
    INCOMPATIBLE_HP_PAIRS[(hp_list[1], hp_list[0])] = reason


def get_incompatibility_reason(hp_a: str, hp_b: str) -> Optional[str]:
    """
    Get the reason why two HP properties are incompatible.
    
    Args:
        hp_a: First HP code (e.g., "HP2")
        hp_b: Second HP code (e.g., "HP3")
    
    Returns:
        Reason string if incompatible, None if compatible
    """
    key = frozenset({hp_a, hp_b})
    return _INCOMPATIBLE_HP_RULES.get(key)


def are_hp_incompatible(hp_a: str, hp_b: str) -> bool:
    """
    Check if two HP properties are incompatible.
    
    Args:
        hp_a: First HP code
        hp_b: Second HP code
    
    Returns:
        True if incompatible, False otherwise
    """
    return frozenset({hp_a, hp_b}) in _INCOMPATIBLE_HP_RULES


def get_all_incompatible_with(hp_code: str) -> List[Tuple[str, str]]:
    """
    Get all HP properties that are incompatible with the given HP.
    
    Args:
        hp_code: HP code to check
    
    Returns:
        List of tuples (incompatible_hp, reason)
    """
    results = []
    for hp_set, reason in _INCOMPATIBLE_HP_RULES.items():
        if hp_code in hp_set:
            other_hp = (hp_set - {hp_code}).pop()
            results.append((other_hp, reason))
    return results


# Special handling rules for HP9 (Infectious)
HP9_SEGREGATION_RULES = {
    "general": "Infectious waste (HP9) should be segregated from all other waste types to prevent contamination and maintain traceability.",
    "exceptions": [
        "HP9 waste may only be mixed with other HP9 waste from the same source and pathogen category.",
    ],
    "treatment_required": "Incineration, autoclaving, or other validated treatment methods required before disposal."
}

# HP14 special rules (changed in 2018)
HP14_RULES = {
    "pre_2018": {
        "description": "Original HP14 criteria based on R50-R53 risk phrases",
        "valid_until": "2018-07-05"
    },
    "post_2018": {
        "description": "New HP14 criteria based on CLP hazard statements for aquatic environment",
        "valid_from": "2018-07-05",
        "hazard_statements": ["H400", "H410", "H411", "H412", "H413"],
        "thresholds": {
            "H400_H410": 0.1,  # 0.1% for Aquatic Acute 1 / Chronic 1
            "H411": 1.0,       # 1% for Aquatic Chronic 2
            "H412": 10.0,      # 10% for Aquatic Chronic 3
            "H413": 25.0,      # 25% for Aquatic Chronic 4 (sum rule)
        }
    }
}


# Severity classification for incompatibilities
SEVERITY_LEVELS = {
    "CRITICAL": {
        "description": "Immediate danger of explosion, fire, or toxic release",
        "pairs": [
            ("HP1", "HP2"), ("HP1", "HP3"), ("HP2", "HP3"),
            ("HP8", "HP12"), ("HP3", "HP12")
        ]
    },
    "HIGH": {
        "description": "Significant risk of hazardous reaction or enhanced toxicity",
        "pairs": [
            ("HP2", "HP6"), ("HP2", "HP8"), ("HP2", "HP11"),
            ("HP3", "HP6"), ("HP6", "HP12")
        ]
    },
    "MEDIUM": {
        "description": "Potential for adverse reactions under certain conditions",
        "pairs": [
            ("HP4", "HP8"), ("HP1", "HP4")
        ]
    }
}


def get_severity(hp_a: str, hp_b: str) -> Optional[str]:
    """
    Get the severity level of an HP incompatibility.
    
    Args:
        hp_a: First HP code
        hp_b: Second HP code
    
    Returns:
        Severity level string or None if compatible
    """
    pair = tuple(sorted([hp_a, hp_b]))
    for level, data in SEVERITY_LEVELS.items():
        if pair in data["pairs"] or (pair[1], pair[0]) in data["pairs"]:
            return level
    return None