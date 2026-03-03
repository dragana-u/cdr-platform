# c:\Users\ncvet\cdr-platform\src\api\waste_api.py
"""
FastAPI REST API for waste compatibility checking.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
import sys

# Add parent directory to path for direct execution
if __name__ == "__main__" or "src.api" not in sys.modules:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.kg.graph_store import WasteKnowledgeGraph
    from src.kg.models import WasteEntry, WasteEntryType, CompatibilityResult
    from src.kg.incompatibility_rules import get_all_incompatible_with
else:
    from ..kg.graph_store import WasteKnowledgeGraph
    from ..kg.models import WasteEntry, WasteEntryType, CompatibilityResult
    from ..kg.incompatibility_rules import get_all_incompatible_with

logger = logging.getLogger(__name__)

# Global knowledge graph instance
kg: Optional[WasteKnowledgeGraph] = None


def get_kg() -> WasteKnowledgeGraph:
    """Get or initialize the knowledge graph."""
    global kg
    if kg is None:
        ontology_path = Path(__file__).parent.parent.parent / "ontology" / "waste-hp.ttl"
        kg = WasteKnowledgeGraph(ontology_path if ontology_path.exists() else None)
    return kg


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info("Initializing knowledge graph...")
    get_kg()
    logger.info("Knowledge graph initialized")
    yield
    # Shutdown
    logger.info("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Waste Compatibility API",
    description="API for checking waste compatibility based on EU List of Waste and HP properties",
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# Pydantic Models for API
# =============================================================================

class WasteEntryResponse(BaseModel):
    """Response model for a waste entry."""
    low_code: str = Field(..., description="List of Waste code (e.g., '11 01 05*')")
    description: str = Field(..., description="Waste description")
    entry_type: str = Field(..., description="Entry type: AH, MH, MNH, ANH")
    hp_properties: List[str] = Field(default_factory=list, description="HP property codes")
    is_hazardous: bool = Field(..., description="Whether the waste is classified as hazardous")
    chapter: Optional[str] = Field(None, description="LoW chapter code")
    subchapter: Optional[str] = Field(None, description="LoW subchapter code")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "low_code": "11 01 05*",
                "description": "pickling acids",
                "entry_type": "AH",
                "hp_properties": ["HP4", "HP8"],
                "is_hazardous": True,
                "chapter": "11",
                "subchapter": "11 01"
            }
        }
    )


class IncompatibilityConflictResponse(BaseModel):
    """Response model for an incompatibility conflict."""
    hp_a: str = Field(..., description="First HP code in conflict")
    hp_b: str = Field(..., description="Second HP code in conflict")
    reason: str = Field(..., description="Reason for incompatibility")
    severity: str = Field(..., description="Severity level: CRITICAL, HIGH, MEDIUM")


class CompatibilityResponse(BaseModel):
    """Response model for compatibility check."""
    compatible: bool = Field(..., description="Whether the wastes are compatible")
    waste_a: str = Field(..., description="First waste code")
    waste_b: str = Field(..., description="Second waste code")
    conflicts: List[IncompatibilityConflictResponse] = Field(
        default_factory=list, 
        description="List of HP conflicts"
    )
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "compatible": False,
                "waste_a": "11 01 05*",
                "waste_b": "07 01 03*",
                "conflicts": [
                    {
                        "hp_a": "HP8",
                        "hp_b": "HP3",
                        "reason": "Corrosive + Flammable materials should not be mixed",
                        "severity": "HIGH"
                    }
                ],
                "warnings": [],
                "recommendations": ["These wastes should be stored and transported separately."]
            }
        }
    )


class CompatibilityRequest(BaseModel):
    """Request model for compatibility check."""
    waste_a: str = Field(..., description="First LoW code")
    waste_b: str = Field(..., description="Second LoW code")


class IncompatibleWasteResponse(BaseModel):
    """Response model for incompatible waste lookup."""
    waste: WasteEntryResponse
    reason: str = Field(..., description="Reason for incompatibility")


class KGStatisticsResponse(BaseModel):
    """Response model for knowledge graph statistics."""
    total_triples: int
    waste_entries: int
    hp_properties: int
    substances: int


class AddWasteRequest(BaseModel):
    """Request model for adding a waste entry."""
    low_code: str = Field(..., description="List of Waste code")
    description: str = Field(..., description="Waste description")
    entry_type: str = Field(..., description="Entry type: AH, MH, MNH, ANH")
    hp_properties: List[str] = Field(default_factory=list, description="HP property codes")
    chapter: Optional[str] = Field(None, description="LoW chapter code")
    subchapter: Optional[str] = Field(None, description="LoW subchapter code")


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Waste Compatibility API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/compatibility", response_model=CompatibilityResponse, tags=["Compatibility"])
async def check_compatibility(request: CompatibilityRequest) -> CompatibilityResponse:
    """
    Check if two waste types are compatible for mixing/storage.
    
    Returns compatibility status along with any conflicts, warnings, and recommendations.
    """
    knowledge_graph = get_kg()
    result = knowledge_graph.check_compatibility(request.waste_a, request.waste_b)
    
    return CompatibilityResponse(
        compatible=result.compatible,
        waste_a=result.waste_a,
        waste_b=result.waste_b,
        conflicts=[
            IncompatibilityConflictResponse(
                hp_a=c.hp_a,
                hp_b=c.hp_b,
                reason=c.reason,
                severity=c.severity
            ) for c in result.conflicts
        ],
        warnings=result.warnings,
        recommendations=result.recommendations
    )


@app.get(
    "/compatibility/check",
    response_model=CompatibilityResponse,
    tags=["Compatibility"]
)
async def check_compatibility_get(
    waste_a: str = Query(..., description="First LoW code"),
    waste_b: str = Query(..., description="Second LoW code")
) -> CompatibilityResponse:
    """
    Check if two waste types are compatible (GET version).
    
    Alternative to POST endpoint for simpler integration.
    """
    request = CompatibilityRequest(waste_a=waste_a, waste_b=waste_b)
    return await check_compatibility(request)


@app.get("/waste/{code}", response_model=WasteEntryResponse, tags=["Waste Entries"])
async def get_waste(code: str) -> WasteEntryResponse:
    """
    Get details of a waste entry by its LoW code.
    
    Returns HP classifications, entry type, and description.
    """
    knowledge_graph = get_kg()
    
    # URL decode the code (spaces might be encoded)
    code = code.replace("%20", " ")
    
    entry = knowledge_graph.get_waste_entry(code)
    
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Waste entry with code '{code}' not found"
        )
    
    return WasteEntryResponse(
        low_code=entry.low_code,
        description=entry.description,
        entry_type=entry.entry_type.value,
        hp_properties=list(entry.hp_properties),
        is_hazardous=entry.is_hazardous,
        chapter=entry.chapter,
        subchapter=entry.subchapter
    )


@app.get(
    "/waste/{code}/incompatible",
    response_model=List[IncompatibleWasteResponse],
    tags=["Compatibility"]
)
async def get_incompatible_wastes(code: str) -> List[IncompatibleWasteResponse]:
    """
    Get all waste entries that are incompatible with the given waste.
    
    Returns list of incompatible wastes with reasons.
    """
    knowledge_graph = get_kg()
    
    # URL decode the code
    code = code.replace("%20", " ")
    
    # Verify the waste exists
    entry = knowledge_graph.get_waste_entry(code)
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Waste entry with code '{code}' not found"
        )
    
    incompatible = knowledge_graph.get_incompatible_wastes(code)
    
    return [
        IncompatibleWasteResponse(
            waste=WasteEntryResponse(
                low_code=w.low_code,
                description=w.description,
                entry_type=w.entry_type.value,
                hp_properties=list(w.hp_properties),
                is_hazardous=w.is_hazardous,
                chapter=w.chapter,
                subchapter=w.subchapter
            ),
            reason=reason
        )
        for w, reason in incompatible
    ]


@app.get("/waste", response_model=List[WasteEntryResponse], tags=["Waste Entries"])
async def list_wastes(
    hp: Optional[str] = Query(None, description="Filter by HP property code"),
    hazardous: Optional[bool] = Query(None, description="Filter by hazardous status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> List[WasteEntryResponse]:
    """
    List waste entries with optional filtering.
    """
    knowledge_graph = get_kg()
    
    if hp:
        entries = knowledge_graph.get_wastes_with_hp(hp)
    else:
        entries = knowledge_graph.get_all_waste_entries()
    
    # Apply hazardous filter if specified
    if hazardous is not None:
        entries = [e for e in entries if e.is_hazardous == hazardous]
    
    # Apply pagination
    entries = entries[offset:offset + limit]
    
    return [
        WasteEntryResponse(
            low_code=e.low_code,
            description=e.description,
            entry_type=e.entry_type.value,
            hp_properties=list(e.hp_properties),
            is_hazardous=e.is_hazardous,
            chapter=e.chapter,
            subchapter=e.subchapter
        )
        for e in entries
    ]


@app.post("/waste", response_model=WasteEntryResponse, tags=["Waste Entries"])
async def add_waste(request: AddWasteRequest) -> WasteEntryResponse:
    """
    Add a new waste entry to the knowledge graph.
    """
    knowledge_graph = get_kg()
    
    # Map string entry type to enum
    entry_type_map = {
        "AH": WasteEntryType.ABSOLUTE_HAZARDOUS,
        "MH": WasteEntryType.MIRROR_HAZARDOUS,
        "MNH": WasteEntryType.MIRROR_NON_HAZARDOUS,
        "ANH": WasteEntryType.ABSOLUTE_NON_HAZARDOUS,
    }
    
    entry_type = entry_type_map.get(request.entry_type.upper())
    if not entry_type:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entry type: {request.entry_type}. Must be one of: AH, MH, MNH, ANH"
        )
    
    entry = WasteEntry(
        low_code=request.low_code,
        description=request.description,
        entry_type=entry_type,
        hp_properties=set(request.hp_properties),
        chapter=request.chapter,
        subchapter=request.subchapter
    )
    
    knowledge_graph.add_waste_entry(entry)
    
    return WasteEntryResponse(
        low_code=entry.low_code,
        description=entry.description,
        entry_type=entry.entry_type.value,
        hp_properties=list(entry.hp_properties),
        is_hazardous=entry.is_hazardous,
        chapter=entry.chapter,
        subchapter=entry.subchapter
    )


@app.get("/hp", tags=["HP Properties"])
async def list_hp_properties() -> Dict[str, Dict[str, str]]:
    """
    List all HP hazardous properties with descriptions.
    """
    return {
        "HP1": {"name": "Explosive", "description": "Waste capable of producing gas at temperature/pressure/speed causing damage"},
        "HP2": {"name": "Oxidising", "description": "Waste that may cause or contribute to combustion of other materials"},
        "HP3": {"name": "Flammable", "description": "Flammable liquid, solid, or gaseous waste"},
        "HP4": {"name": "Irritant", "description": "Waste that can cause skin irritation or eye damage"},
        "HP5": {"name": "STOT/Aspiration Toxicity", "description": "Waste causing specific target organ toxicity or aspiration hazard"},
        "HP6": {"name": "Acute Toxicity", "description": "Waste causing acute toxic effects via oral, dermal, or inhalation"},
        "HP7": {"name": "Carcinogenic", "description": "Waste that induces cancer or increases its incidence"},
        "HP8": {"name": "Corrosive", "description": "Waste that can cause skin corrosion"},
        "HP9": {"name": "Infectious", "description": "Waste containing viable pathogens known to cause disease"},
        "HP10": {"name": "Toxic for Reproduction", "description": "Waste with adverse effects on sexual function, fertility, or development"},
        "HP11": {"name": "Mutagenic", "description": "Waste that may cause genetic mutations"},
        "HP12": {"name": "Release of Acute Toxic Gas", "description": "Waste releasing toxic gases on contact with water or acid"},
        "HP13": {"name": "Sensitising", "description": "Waste containing substances that cause sensitisation"},
        "HP14": {"name": "Ecotoxic", "description": "Waste presenting risks to the environment"},
        "HP15": {"name": "Yielding Another Hazardous Property", "description": "Waste capable of exhibiting hazardous properties not directly displayed"},
    }


@app.get("/hp/{code}/incompatible", tags=["HP Properties"])
async def get_hp_incompatibilities(code: str) -> List[Dict[str, str]]:
    """
    Get all HP properties that are incompatible with the given HP.
    """
    code = code.upper()
    if not code.startswith("HP"):
        code = f"HP{code}"
    
    incompatible = get_all_incompatible_with(code)
    
    return [
        {"hp_code": hp, "reason": reason}
        for hp, reason in incompatible
    ]


@app.get("/stats", response_model=KGStatisticsResponse, tags=["General"])
async def get_statistics() -> KGStatisticsResponse:
    """
    Get statistics about the knowledge graph.
    """
    knowledge_graph = get_kg()
    stats = knowledge_graph.get_statistics()
    
    return KGStatisticsResponse(**stats)


@app.post("/query", tags=["Advanced"])
async def execute_sparql_query(
    query: str = Query(..., description="SPARQL query string")
) -> List[Dict[str, Any]]:
    """
    Execute a SPARQL query against the knowledge graph.
    
    For advanced users who need flexible querying capabilities.
    """
    knowledge_graph = get_kg()
    
    try:
        results = knowledge_graph.query(query)
        # Convert RDF terms to strings for JSON serialization
        return [
            {k: str(v) if v else None for k, v in row.items()}
            for row in results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"SPARQL query error: {str(e)}"
        )