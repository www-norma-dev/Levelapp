"""
'firestore/schemas.py': Defines Pydantic models for Firestore data structures.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DocType(Enum):
    SCENARIO = "scenario"
    BUNDLE = "metadata"


class ScenarioBatch(BaseModel):
    metadata: Optional[Dict[str, Any]] = None
    content: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scenarios: List[Any] = Field(default_factory=list)

class ExtractionBundle(BaseModel):
    content: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
