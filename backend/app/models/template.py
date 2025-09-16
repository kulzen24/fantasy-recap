"""
Template models for user-uploaded style samples
Handles uploaded recap samples and their analysis
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from app.models.llm import RecapTone, RecapLength


class TemplateStatus(str, Enum):
    """Status of a template"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"
    ARCHIVED = "archived"


class FileFormat(str, Enum):
    """Supported file formats"""
    TXT = "txt"
    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"
    MD = "md"


class StyleAnalysis(BaseModel):
    """Analysis results for a template"""
    # Tone analysis
    tone: RecapTone
    tone_confidence: float = Field(ge=0, le=1, description="Confidence score for tone detection")
    
    # Style characteristics
    formality_level: float = Field(ge=0, le=1, description="0=casual, 1=formal")
    humor_level: float = Field(ge=0, le=1, description="0=serious, 1=humorous")
    emotion_intensity: float = Field(ge=0, le=1, description="0=neutral, 1=highly emotional")
    
    # Writing characteristics
    avg_sentence_length: float
    vocabulary_complexity: float = Field(ge=0, le=1, description="0=simple, 1=complex")
    use_of_metaphors: bool
    use_of_statistics: bool
    
    # Structure analysis
    has_intro: bool
    has_conclusion: bool
    uses_headers: bool
    paragraph_count: int
    
    # Content patterns
    focuses_on_winners: bool
    focuses_on_losers: bool
    includes_predictions: bool
    includes_awards: bool
    mentions_specific_players: bool
    
    # Linguistic features
    common_phrases: List[str] = Field(default_factory=list)
    signature_words: List[str] = Field(default_factory=list)
    writing_patterns: Dict[str, Any] = Field(default_factory=dict)


class PromptTemplate(BaseModel):
    """Generated prompt template for LLM"""
    template_id: str
    user_id: str
    
    # Template content
    system_prompt: str = Field(description="System-level prompt for LLM")
    style_instructions: str = Field(description="Style-specific instructions")
    structure_template: str = Field(description="Template for content structure")
    
    # Metadata
    based_on_analysis: StyleAnalysis
    generated_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    # Settings
    is_active: bool = True
    is_default: bool = False


class UserTemplate(BaseModel):
    """User-uploaded template and its analysis"""
    id: str
    user_id: str
    
    # File information
    filename: str
    file_format: FileFormat
    file_size: int  # in bytes
    file_hash: str = Field(description="SHA-256 hash for deduplication")
    
    # Storage
    storage_path: str = Field(description="Path to stored file")
    
    # Content
    extracted_text: Optional[str] = None
    word_count: Optional[int] = None
    
    # Processing
    status: TemplateStatus = TemplateStatus.UPLOADED
    upload_date: datetime
    analysis_date: Optional[datetime] = None
    
    # Analysis results
    style_analysis: Optional[StyleAnalysis] = None
    generated_prompt: Optional[PromptTemplate] = None
    
    # Metadata
    user_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Settings
    is_active: bool = True
    is_favorite: bool = False


class TemplateUploadRequest(BaseModel):
    """Request for uploading a new template"""
    filename: str
    file_content: bytes = Field(description="Base64 encoded file content")
    file_format: FileFormat
    user_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TemplateAnalysisRequest(BaseModel):
    """Request for analyzing a template"""
    template_id: str
    force_reanalysis: bool = False


class TemplateListResponse(BaseModel):
    """Response for listing user templates"""
    templates: List[UserTemplate]
    total: int
    page: int
    page_size: int


class TemplateAnalysisResponse(BaseModel):
    """Response for template analysis"""
    template_id: str
    status: TemplateStatus
    analysis: Optional[StyleAnalysis] = None
    prompt_template: Optional[PromptTemplate] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
