"""
levelapp_core_simulators/schemas.py: Generic Pydantic models for simulator data structures.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum

class InteractionType(str, Enum):
    """Enum representing the type of interaction."""
    OPENING = "opening"
    DEVELOPMENT = "development"
    CLOSURE = "closure"

class InteractionDetails(BaseModel):
    """Model representing details of a simulated interaction."""
    reply: Optional[str] = "No response"
    extracted_metadata: Optional[Dict[str, Any]] = {}
    handoff_details: Optional[Dict[str, Any]] = {}
    interaction_type: Optional[InteractionType] = InteractionType.OPENING

class InteractionEvaluationResult(BaseModel):
    """Model representing the evaluation result of an interaction."""
    evaluations: Dict[str, Any] 
    extracted_metadata_evaluation: float
    scenario_id: str

class Interaction(BaseModel):
    """Represents a single interaction within a conversation."""
    id: UUID = Field(default_factory=uuid4, description="Interaction identifier")
    user_message: str = Field(..., description="The user's message")
    agent_reply: str = Field(..., description="The agent's response message")
    reference_reply: str = Field(..., description="The expected reference message")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    reference_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Expected metadata for this interaction")
    generated_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generated metadata from the agent's response")

class BasicConversation(BaseModel):
    """Represents a basic conversation with multiple interactions."""
    id: UUID = Field(default_factory=uuid4, description="Conversation identifier")
    interactions: List[Interaction] = Field(default_factory=list, description="List of interactions in the conversation")
    description: str = Field(..., description="A short description of the conversation")
    details: Dict[str, str] = Field(default_factory=dict, description="Conversation details")

class ConversationBatch(BaseModel):
    conversations: List[BasicConversation] = Field(default_factory=list, description="List of conversations in the batch")