# c:\Users\ncvet\cdr-platform\src\kg\graph_store.py
"""
RDF Knowledge Graph store for waste classification data.
Uses RDFLib for graph storage and SPARQL queries.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set, Dict, Any, Tuple
from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, OWL, XSD
from rdflib.namespace import NamespaceManager

from .models import (
    WasteEntry, WasteEntryType, HazardousProperty, 
    CompatibilityResult, Substance, CLPHazardStatement
)
from .incompatibility_rules import (
    INCOMPATIBLE_HP_PAIRS, get_incompatibility_reason, 
    get_severity, HP9_SEGREGATION_RULES
)

logger = logging.getLogger(__name__)

# Define namespaces
WASTE = Namespace("http://example.org/waste-hp#")
ENVO = Namespace("http://purl.obolibrary.org/obo/ENVO_")
CHEBI = Namespace("http://purl.obolibrary.org/obo/CHEBI_")
SOSA = Namespace("http://www.w3.org/ns/sosa/")


class WasteKnowledgeGraph:
    """
    Knowledge graph for waste classification and compatibility checking.
    
    Uses RDFLib for storage and SPARQL for queries.
    """
    
    def __init__(self, ontology_path: Optional[Path] = None):
        """
        Initialize the knowledge graph.
        
        Args:
            ontology_path: Path to the waste-hp.ttl ontology file
        """
        self.graph = Graph()
        self._bind_namespaces()
        
        if ontology_path and ontology_path.exists():
            self.load_ontology(ontology_path)
            logger.info(f"Loaded ontology from {ontology_path}")
    
    def _bind_namespaces(self):
        """Bind common namespaces to the graph."""
        self.graph.bind("waste", WASTE)
        self.graph.bind("envo", ENVO)
        self.graph.bind("chebi", CHEBI)
        self.graph.bind("sosa", SOSA)
        self.graph.bind("owl", OWL)
    
    def load_ontology(self, path: Path):
        """Load an ontology file into the graph."""
        self.graph.parse(path, format="turtle")
    
    def load_rdf(self, path: Path, format: str = "turtle"):
        """Load RDF data from a file."""
        self.graph.parse(path, format=format)
    
    def save(self, path: Path, format: str = "turtle"):
        """Save the graph to a file."""
        self.graph.serialize(destination=path, format=format)
    
    # =========================================================================
    # Waste Entry Operations
    # =========================================================================
    
    def add_waste_entry(self, entry: WasteEntry) -> URIRef:
        """
        Add a waste entry to the knowledge graph.
        
        Args:
            entry: WasteEntry object to add
        
        Returns:
            URI of the created resource
        """
        # Create URI for the waste entry (normalize code for URI)
        uri_code = entry.low_code.replace(" ", "_").replace("*", "_star")
        waste_uri = WASTE[f"waste_{uri_code}"]
        
        # Add basic triples
        self.graph.add((waste_uri, RDF.type, WASTE.WasteEntry))
        self.graph.add((waste_uri, WASTE.lowCode, Literal(entry.low_code)))
        self.graph.add((waste_uri, WASTE.description, Literal(entry.description)))
        
        # Add entry type
        entry_type_uri = self._get_entry_type_uri(entry.entry_type)
        self.graph.add((waste_uri, WASTE.hasEntryType, entry_type_uri))
        
        # Add HP properties
        for hp_code in entry.hp_properties:
            hp_uri = WASTE[hp_code]
            self.graph.add((waste_uri, WASTE.hasHP, hp_uri))
            self.graph.add((hp_uri, RDF.type, WASTE.HazardousProperty))
            self.graph.add((hp_uri, WASTE.hpCode, Literal(hp_code)))
        
        # Add chapter info if present
        if entry.chapter:
            self.graph.add((waste_uri, WASTE.chapter, Literal(entry.chapter)))
        if entry.subchapter:
            self.graph.add((waste_uri, WASTE.subchapter, Literal(entry.subchapter)))
        
        logger.debug(f"Added waste entry: {entry.low_code}")
        return waste_uri
    
    def _get_entry_type_uri(self, entry_type: WasteEntryType) -> URIRef:
        """Get the URI for a waste entry type."""
        type_mapping = {
            WasteEntryType.ABSOLUTE_HAZARDOUS: WASTE.AbsoluteHazardous,
            WasteEntryType.MIRROR_HAZARDOUS: WASTE.MirrorHazardous,
            WasteEntryType.MIRROR_NON_HAZARDOUS: WASTE.MirrorNonHazardous,
            WasteEntryType.ABSOLUTE_NON_HAZARDOUS: WASTE.AbsoluteNonHazardous,
        }
        return type_mapping.get(entry_type, WASTE.AbsoluteNonHazardous)
    
    def get_waste_entry(self, low_code: str) -> Optional[WasteEntry]:
        """
        Retrieve a waste entry by its LoW code.
        
        Args:
            low_code: The List of Waste code (e.g., "11 01 05*")
        
        Returns:
            WasteEntry object or None if not found
        """
        query = """
        PREFIX waste: <http://example.org/waste-hp#>
        
        SELECT ?uri ?description ?entryType ?chapter ?subchapter
        WHERE {
            ?uri a waste:WasteEntry ;
                 waste:lowCode ?code ;
                 waste:description ?description .
            FILTER(?code = ?targetCode)
            OPTIONAL { ?uri waste:hasEntryType ?entryType }
            OPTIONAL { ?uri waste:chapter ?chapter }
            OPTIONAL { ?uri waste:subchapter ?subchapter }
        }
        """
        
        results = self.graph.query(query, initBindings={"targetCode": Literal(low_code)})
        
        for row in results:
            # Get HP properties for this waste
            hp_properties = self._get_hp_properties_for_waste(row.uri)
            
            # Determine entry type
            entry_type = self._uri_to_entry_type(row.entryType)
            
            return WasteEntry(
                low_code=low_code,
                description=str(row.description),
                entry_type=entry_type,
                hp_properties=hp_properties,
                chapter=str(row.chapter) if row.chapter else None,
                subchapter=str(row.subchapter) if row.subchapter else None
            )
        
        return None
    
    def _get_hp_properties_for_waste(self, waste_uri: URIRef) -> Set[str]:
        """Get all HP properties for a waste entry."""
        query = """
        PREFIX waste: <http://example.org/waste-hp#>
        
        SELECT ?hpCode
        WHERE {
            ?waste waste:hasHP ?hp .
            ?hp waste:hpCode ?hpCode .
        }
        """
        
        results = self.graph.query(query, initBindings={"waste": waste_uri})
        return {str(row.hpCode) for row in results}
    
    def _uri_to_entry_type(self, uri: Optional[URIRef]) -> WasteEntryType:
        """Convert a URI to WasteEntryType enum."""
        if uri is None:
            return WasteEntryType.ABSOLUTE_NON_HAZARDOUS
        
        uri_str = str(uri)
        if "AbsoluteHazardous" in uri_str:
            return WasteEntryType.ABSOLUTE_HAZARDOUS
        elif "MirrorHazardous" in uri_str:
            return WasteEntryType.MIRROR_HAZARDOUS
        elif "MirrorNonHazardous" in uri_str:
            return WasteEntryType.MIRROR_NON_HAZARDOUS
        else:
            return WasteEntryType.ABSOLUTE_NON_HAZARDOUS
    
    def get_all_waste_entries(self) -> List[WasteEntry]:
        """Get all waste entries in the knowledge graph."""
        query = """
        PREFIX waste: <http://example.org/waste-hp#>
        
        SELECT ?uri ?code ?description ?entryType
        WHERE {
            ?uri a waste:WasteEntry ;
                 waste:lowCode ?code ;
                 waste:description ?description .
            OPTIONAL { ?uri waste:hasEntryType ?entryType }
        }
        ORDER BY ?code
        """
        
        entries = []
        results = self.graph.query(query)
        
        for row in results:
            hp_properties = self._get_hp_properties_for_waste(row.uri)
            entry_type = self._uri_to_entry_type(row.entryType)
            
            entries.append(WasteEntry(
                low_code=str(row.code),
                description=str(row.description),
                entry_type=entry_type,
                hp_properties=hp_properties
            ))
        
        return entries
    
    # =========================================================================
    # HP Property Operations
    # =========================================================================
    
    def get_hp_properties(self, waste_code: str) -> Set[str]:
        """
        Get HP properties for a waste code.
        
        Args:
            waste_code: The LoW code
        
        Returns:
            Set of HP codes (e.g., {"HP3", "HP6"})
        """
        query = """
        PREFIX waste: <http://example.org/waste-hp#>
        
        SELECT ?hpCode
        WHERE {
            ?waste a waste:WasteEntry ;
                   waste:lowCode ?code ;
                   waste:hasHP ?hp .
            ?hp waste:hpCode ?hpCode .
            FILTER(?code = ?targetCode)
        }
        """
        
        results = self.graph.query(query, initBindings={"targetCode": Literal(waste_code)})
        return {str(row.hpCode) for row in results}
    
    def get_wastes_with_hp(self, hp_code: str) -> List[WasteEntry]:
        """
        Get all waste entries that have a specific HP property.
        
        Args:
            hp_code: HP code (e.g., "HP3")
        
        Returns:
            List of WasteEntry objects
        """
        query = """
        PREFIX waste: <http://example.org/waste-hp#>
        
        SELECT ?uri ?code ?description ?entryType
        WHERE {
            ?uri a waste:WasteEntry ;
                 waste:lowCode ?code ;
                 waste:description ?description ;
                 waste:hasHP ?hp .
            ?hp waste:hpCode ?hpCode .
            FILTER(?hpCode = ?targetHP)
            OPTIONAL { ?uri waste:hasEntryType ?entryType }
        }
        """
        
        entries = []
        results = self.graph.query(query, initBindings={"targetHP": Literal(hp_code)})
        
        for row in results:
            hp_properties = self._get_hp_properties_for_waste(row.uri)
            entry_type = self._uri_to_entry_type(row.entryType)
            
            entries.append(WasteEntry(
                low_code=str(row.code),
                description=str(row.description),
                entry_type=entry_type,
                hp_properties=hp_properties
            ))
        
        return entries
    
    # =========================================================================
    # Compatibility Checking
    # =========================================================================
    
    def check_compatibility(self, waste_code_a: str, waste_code_b: str) -> CompatibilityResult:
        """
        Check if two waste types are compatible for mixing/storage.
        
        Args:
            waste_code_a: First LoW code
            waste_code_b: Second LoW code
        
        Returns:
            CompatibilityResult with compatibility status and any conflicts
        """
        result = CompatibilityResult(
            compatible=True,
            waste_a=waste_code_a,
            waste_b=waste_code_b
        )
        
        # Get HP properties for both wastes
        hps_a = self.get_hp_properties(waste_code_a)
        hps_b = self.get_hp_properties(waste_code_b)
        
        # If we couldn't find HP data, add warnings
        if not hps_a:
            waste_a = self.get_waste_entry(waste_code_a)
            if waste_a and waste_a.entry_type == WasteEntryType.MIRROR_HAZARDOUS:
                result.add_warning(
                    f"Waste {waste_code_a} is Mirror Hazardous - HP properties need assessment. "
                    "Treating conservatively as potentially hazardous."
                )
                # For MH entries without known HPs, we can't determine compatibility
            elif not waste_a:
                result.add_warning(f"Waste {waste_code_a} not found in knowledge graph")
        
        if not hps_b:
            waste_b = self.get_waste_entry(waste_code_b)
            if waste_b and waste_b.entry_type == WasteEntryType.MIRROR_HAZARDOUS:
                result.add_warning(
                    f"Waste {waste_code_b} is Mirror Hazardous - HP properties need assessment. "
                    "Treating conservatively as potentially hazardous."
                )
            elif not waste_b:
                result.add_warning(f"Waste {waste_code_b} not found in knowledge graph")
        
        # Check HP9 (Infectious) segregation rules
        if "HP9" in hps_a or "HP9" in hps_b:
            if "HP9" in hps_a and "HP9" not in hps_b:
                result.add_conflict(
                    "HP9", "N/A",
                    HP9_SEGREGATION_RULES["general"],
                    severity="HIGH"
                )
            elif "HP9" in hps_b and "HP9" not in hps_a:
                result.add_conflict(
                    "N/A", "HP9",
                    HP9_SEGREGATION_RULES["general"],
                    severity="HIGH"
                )
            # Both HP9 - add warning about same source requirement
            elif "HP9" in hps_a and "HP9" in hps_b:
                result.add_warning(
                    "Both wastes are HP9 (Infectious). Verify they are from the same "
                    "source and pathogen category before mixing."
                )
        
        # Check all HP pair incompatibilities
        for hp_a in hps_a:
            for hp_b in hps_b:
                reason = get_incompatibility_reason(hp_a, hp_b)
                if reason:
                    severity = get_severity(hp_a, hp_b) or "HIGH"
                    result.add_conflict(hp_a, hp_b, reason, severity)
        
        # Check same-HP conflicts (e.g., two HP12 wastes)
        common_hps = hps_a & hps_b
        for hp in common_hps:
            if hp == "HP12":
                result.add_warning(
                    "Both wastes have HP12 (Release of Acute Toxic Gas). "
                    "Mixing may result in cumulative toxic gas release."
                )
            elif hp == "HP1":
                result.add_warning(
                    "Both wastes are HP1 (Explosive). "
                    "Special handling required - consult explosives expert."
                )
        
        # Add recommendations based on conflicts
        if not result.compatible:
            result.add_recommendation(
                "These wastes should be stored and transported separately."
            )
            if any(c.severity == "CRITICAL" for c in result.conflicts):
                result.add_recommendation(
                    "CRITICAL: Immediate separation required. Risk of explosion, fire, or toxic release."
                )
        
        return result
    
    def get_incompatible_wastes(self, waste_code: str) -> List[Tuple[WasteEntry, str]]:
        """
        Get all waste entries that are incompatible with the given waste.
        
        Args:
            waste_code: LoW code to check against
        
        Returns:
            List of tuples (WasteEntry, reason)
        """
        incompatible = []
        hps = self.get_hp_properties(waste_code)
        
        # Get all HPs that are incompatible with our waste's HPs
        incompatible_hps = set()
        for hp in hps:
            for (hp_a, hp_b), reason in INCOMPATIBLE_HP_PAIRS.items():
                if hp_a == hp:
                    incompatible_hps.add(hp_b)
                elif hp_b == hp:
                    incompatible_hps.add(hp_a)
        
        # Find all wastes with those incompatible HPs
        for hp in incompatible_hps:
            wastes = self.get_wastes_with_hp(hp)
            for waste in wastes:
                if waste.low_code != waste_code:
                    # Get the specific reason
                    for my_hp in hps:
                        reason = get_incompatibility_reason(my_hp, hp)
                        if reason:
                            incompatible.append((waste, reason))
                            break
        
        return incompatible
    
    # =========================================================================
    # SPARQL Query Interface
    # =========================================================================
    
    def query(self, sparql: str, bindings: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Execute a SPARQL query and return results as list of dicts.
        
        Args:
            sparql: SPARQL query string
            bindings: Optional variable bindings
        
        Returns:
            List of result dictionaries
        """
        if bindings:
            results = self.graph.query(sparql, initBindings=bindings)
        else:
            results = self.graph.query(sparql)
        
        return [
            {str(var): row[var] for var in results.vars}
            for row in results
        ]
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the knowledge graph."""
        return {
            "total_triples": len(self.graph),
            "waste_entries": len(list(self.graph.subjects(RDF.type, WASTE.WasteEntry))),
            "hp_properties": len(list(self.graph.subjects(RDF.type, WASTE.HazardousProperty))),
            "substances": len(list(self.graph.subjects(RDF.type, WASTE.Substance))),
        }