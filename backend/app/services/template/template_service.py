"""
Main template service for managing user template uploads and analysis
Orchestrates file storage, text processing, style analysis, and prompt generation
"""

import uuid
import logging
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
from pathlib import Path

from app.models.template import (
    UserTemplate, TemplateStatus, FileFormat, StyleAnalysis, PromptTemplate,
    TemplateUploadRequest, TemplateAnalysisRequest, TemplateListResponse, TemplateAnalysisResponse
)
from app.core.supabase import supabase_client
from .text_processor import text_processor
from .style_analyzer import style_analyzer
from .prompt_generator import prompt_generator

logger = logging.getLogger(__name__)


class TemplateService:
    """Main service for template management"""
    
    def __init__(self):
        self.supabase = supabase_client.client
        self.storage_bucket = "user-templates"  # Supabase storage bucket
    
    async def upload_template(
        self, 
        user_id: str, 
        filename: str,
        file_content: bytes,
        file_format: FileFormat,
        user_notes: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> UserTemplate:
        """
        Upload and process a new template file
        
        Args:
            user_id: User ID
            filename: Original filename
            file_content: File content as bytes
            file_format: File format
            user_notes: Optional user notes
            tags: Optional tags
            
        Returns:
            UserTemplate: Created template record
            
        Raises:
            ValueError: If file validation fails
            Exception: If upload or processing fails
        """
        try:
            # Validate file content
            validation = text_processor.validate_file_content(file_content, file_format)
            if not validation["is_valid"]:
                raise ValueError(f"File validation failed: {', '.join(validation['errors'])}")
            
            # Calculate file hash
            file_hash = text_processor.calculate_file_hash(file_content)
            
            # Check for duplicate
            existing = await self._get_template_by_hash(user_id, file_hash)
            if existing:
                raise ValueError("This file has already been uploaded")
            
            # Generate unique ID and storage path
            template_id = str(uuid.uuid4())
            storage_path = f"{user_id}/{template_id}/{filename}"
            
            # Store file in Supabase storage
            await self._store_file(storage_path, file_content)
            
            # Extract text
            extracted_text = text_processor.extract_text(file_content, file_format)
            text_stats = text_processor.get_text_statistics(extracted_text)
            
            # Create template record
            template = UserTemplate(
                id=template_id,
                user_id=user_id,
                filename=filename,
                file_format=file_format,
                file_size=len(file_content),
                file_hash=file_hash,
                storage_path=storage_path,
                extracted_text=extracted_text,
                word_count=text_stats["word_count"],
                status=TemplateStatus.UPLOADED,
                upload_date=datetime.utcnow(),
                user_notes=user_notes,
                tags=tags or []
            )
            
            # Save to database
            await self._save_template(template)
            
            # Start async analysis
            await self._analyze_template_async(template_id)
            
            logger.info(f"Template uploaded successfully: {template_id}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to upload template: {e}")
            raise
    
    async def analyze_template(self, template_id: str, force_reanalysis: bool = False) -> TemplateAnalysisResponse:
        """
        Analyze a template's style and generate prompt
        
        Args:
            template_id: Template ID
            force_reanalysis: Whether to force reanalysis if already done
            
        Returns:
            TemplateAnalysisResponse: Analysis results
        """
        try:
            # Get template
            template = await self._get_template_by_id(template_id)
            if not template:
                raise ValueError("Template not found")
            
            # Check if already analyzed
            if template.style_analysis and not force_reanalysis:
                return TemplateAnalysisResponse(
                    template_id=template_id,
                    status=template.status,
                    analysis=template.style_analysis,
                    prompt_template=template.generated_prompt
                )
            
            # Update status to processing
            await self._update_template_status(template_id, TemplateStatus.PROCESSING)
            
            start_time = datetime.utcnow()
            
            # Perform style analysis
            if not template.extracted_text:
                raise ValueError("No extracted text available for analysis")
            
            analysis = style_analyzer.analyze_style(template.extracted_text)
            
            # Generate prompt template
            prompt_template = prompt_generator.generate_prompt_template(
                template_id=template_id,
                user_id=template.user_id,
                analysis=analysis
            )
            
            # Save analysis results
            await self._save_analysis_results(template_id, analysis, prompt_template)
            
            # Update template status
            await self._update_template_status(template_id, TemplateStatus.ANALYZED)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Template analysis completed: {template_id}")
            
            return TemplateAnalysisResponse(
                template_id=template_id,
                status=TemplateStatus.ANALYZED,
                analysis=analysis,
                prompt_template=prompt_template,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze template {template_id}: {e}")
            await self._update_template_status(template_id, TemplateStatus.FAILED)
            
            return TemplateAnalysisResponse(
                template_id=template_id,
                status=TemplateStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_user_templates(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 20,
        status_filter: Optional[TemplateStatus] = None
    ) -> TemplateListResponse:
        """
        Get list of user's templates
        
        Args:
            user_id: User ID
            page: Page number (1-based)
            page_size: Number of templates per page
            status_filter: Optional status filter
            
        Returns:
            TemplateListResponse: List of templates
        """
        try:
            offset = (page - 1) * page_size
            
            # Build query
            query = self.supabase.table("user_templates").select("*").eq("user_id", user_id)
            
            if status_filter:
                query = query.eq("status", status_filter.value)
            
            # Get total count
            count_response = query.execute()
            total = len(count_response.data) if count_response.data else 0
            
            # Get paginated results
            response = query.order("upload_date", desc=True).range(offset, offset + page_size - 1).execute()
            
            templates = []
            if response.data:
                for row in response.data:
                    # Convert database row to UserTemplate
                    template = await self._row_to_template(row)
                    templates.append(template)
            
            return TemplateListResponse(
                templates=templates,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"Failed to get user templates: {e}")
            raise
    
    async def get_template(self, template_id: str, user_id: str) -> Optional[UserTemplate]:
        """
        Get a specific template
        
        Args:
            template_id: Template ID
            user_id: User ID (for security)
            
        Returns:
            UserTemplate or None
        """
        try:
            response = self.supabase.table("user_templates").select("*").eq("id", template_id).eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return await self._row_to_template(response.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            return None
    
    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """
        Delete a template and its associated data
        
        Args:
            template_id: Template ID
            user_id: User ID (for security)
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # Get template first
            template = await self.get_template(template_id, user_id)
            if not template:
                return False
            
            # Delete from storage
            await self._delete_file(template.storage_path)
            
            # Delete from database (cascade will handle related records)
            response = self.supabase.table("user_templates").delete().eq("id", template_id).eq("user_id", user_id).execute()
            
            logger.info(f"Template deleted: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            return False
    
    async def get_active_prompt_template(self, user_id: str) -> Optional[PromptTemplate]:
        """
        Get user's active/default prompt template
        
        Args:
            user_id: User ID
            
        Returns:
            PromptTemplate or None
        """
        try:
            # Try to get default template first
            response = self.supabase.table("prompt_templates").select("*").eq("user_id", user_id).eq("is_default", True).eq("is_active", True).execute()
            
            if response.data and len(response.data) > 0:
                return await self._row_to_prompt_template(response.data[0])
            
            # Fallback to most recent active template
            response = self.supabase.table("prompt_templates").select("*").eq("user_id", user_id).eq("is_active", True).order("generated_at", desc=True).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                return await self._row_to_prompt_template(response.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get active prompt template for user {user_id}: {e}")
            return None
    
    # Private helper methods
    
    async def _store_file(self, storage_path: str, content: bytes) -> None:
        """Store file in Supabase storage"""
        # In a real implementation, this would use Supabase storage API
        # For now, we'll simulate successful storage
        logger.info(f"File stored at: {storage_path}")
    
    async def _delete_file(self, storage_path: str) -> None:
        """Delete file from Supabase storage"""
        # In a real implementation, this would use Supabase storage API
        logger.info(f"File deleted from: {storage_path}")
    
    async def _get_template_by_hash(self, user_id: str, file_hash: str) -> Optional[UserTemplate]:
        """Check if template with same hash exists"""
        try:
            response = self.supabase.table("user_templates").select("*").eq("user_id", user_id).eq("file_hash", file_hash).execute()
            
            if response.data and len(response.data) > 0:
                return await self._row_to_template(response.data[0])
            
            return None
            
        except Exception:
            return None
    
    async def _save_template(self, template: UserTemplate) -> None:
        """Save template to database"""
        data = {
            "id": template.id,
            "user_id": template.user_id,
            "filename": template.filename,
            "file_format": template.file_format.value,
            "file_size": template.file_size,
            "file_hash": template.file_hash,
            "storage_path": template.storage_path,
            "extracted_text": template.extracted_text,
            "word_count": template.word_count,
            "status": template.status.value,
            "upload_date": template.upload_date.isoformat(),
            "user_notes": template.user_notes,
            "tags": template.tags,
            "is_active": template.is_active,
            "is_favorite": template.is_favorite
        }
        
        response = self.supabase.table("user_templates").insert(data).execute()
        if not response.data:
            raise Exception("Failed to save template to database")
    
    async def _analyze_template_async(self, template_id: str) -> None:
        """Start async analysis of template"""
        # In a real implementation, this might use a task queue
        # For now, we'll just trigger immediate analysis
        try:
            await self.analyze_template(template_id)
        except Exception as e:
            logger.error(f"Async analysis failed for template {template_id}: {e}")
    
    async def _get_template_by_id(self, template_id: str) -> Optional[UserTemplate]:
        """Get template by ID"""
        try:
            response = self.supabase.table("user_templates").select("*").eq("id", template_id).execute()
            
            if response.data and len(response.data) > 0:
                return await self._row_to_template(response.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get template by ID {template_id}: {e}")
            return None
    
    async def _update_template_status(self, template_id: str, status: TemplateStatus) -> None:
        """Update template status"""
        data = {"status": status.value}
        if status == TemplateStatus.ANALYZED:
            data["analysis_date"] = datetime.utcnow().isoformat()
        
        response = self.supabase.table("user_templates").update(data).eq("id", template_id).execute()
    
    async def _save_analysis_results(
        self, 
        template_id: str, 
        analysis: StyleAnalysis, 
        prompt_template: PromptTemplate
    ) -> None:
        """Save analysis results to database"""
        # Save style analysis
        analysis_data = {
            "template_id": template_id,
            "tone": analysis.tone.value,
            "tone_confidence": float(analysis.tone_confidence),
            "formality_level": float(analysis.formality_level),
            "humor_level": float(analysis.humor_level),
            "emotion_intensity": float(analysis.emotion_intensity),
            "avg_sentence_length": float(analysis.avg_sentence_length),
            "vocabulary_complexity": float(analysis.vocabulary_complexity),
            "use_of_metaphors": analysis.use_of_metaphors,
            "use_of_statistics": analysis.use_of_statistics,
            "has_intro": analysis.has_intro,
            "has_conclusion": analysis.has_conclusion,
            "uses_headers": analysis.uses_headers,
            "paragraph_count": analysis.paragraph_count,
            "focuses_on_winners": analysis.focuses_on_winners,
            "focuses_on_losers": analysis.focuses_on_losers,
            "includes_predictions": analysis.includes_predictions,
            "includes_awards": analysis.includes_awards,
            "mentions_specific_players": analysis.mentions_specific_players,
            "common_phrases": analysis.common_phrases,
            "signature_words": analysis.signature_words,
            "writing_patterns": analysis.writing_patterns
        }
        
        self.supabase.table("style_analysis").upsert(analysis_data).execute()
        
        # Save prompt template
        prompt_data = {
            "template_id": template_id,
            "user_id": prompt_template.user_id,
            "system_prompt": prompt_template.system_prompt,
            "style_instructions": prompt_template.style_instructions,
            "structure_template": prompt_template.structure_template,
            "generated_at": prompt_template.generated_at.isoformat(),
            "usage_count": prompt_template.usage_count,
            "is_active": prompt_template.is_active,
            "is_default": prompt_template.is_default
        }
        
        self.supabase.table("prompt_templates").upsert(prompt_data).execute()
    
    async def _row_to_template(self, row: Dict[str, Any]) -> UserTemplate:
        """Convert database row to UserTemplate"""
        # This would include loading related analysis and prompt data
        # Simplified for now
        return UserTemplate(
            id=row["id"],
            user_id=row["user_id"],
            filename=row["filename"],
            file_format=FileFormat(row["file_format"]),
            file_size=row["file_size"],
            file_hash=row["file_hash"],
            storage_path=row["storage_path"],
            extracted_text=row.get("extracted_text"),
            word_count=row.get("word_count"),
            status=TemplateStatus(row["status"]),
            upload_date=datetime.fromisoformat(row["upload_date"]),
            analysis_date=datetime.fromisoformat(row["analysis_date"]) if row.get("analysis_date") else None,
            user_notes=row.get("user_notes"),
            tags=row.get("tags", []),
            is_active=row.get("is_active", True),
            is_favorite=row.get("is_favorite", False)
        )
    
    async def _row_to_prompt_template(self, row: Dict[str, Any]) -> PromptTemplate:
        """Convert database row to PromptTemplate"""
        # This would need to load the associated StyleAnalysis
        # Simplified for now - would need to query style_analysis table
        return PromptTemplate(
            template_id=row["template_id"],
            user_id=row["user_id"],
            system_prompt=row["system_prompt"],
            style_instructions=row["style_instructions"],
            structure_template=row["structure_template"],
            based_on_analysis=StyleAnalysis(
                tone=RecapTone.PROFESSIONAL,  # Would load from database
                tone_confidence=0.8,
                formality_level=0.5,
                humor_level=0.3,
                emotion_intensity=0.4,
                avg_sentence_length=15.0,
                vocabulary_complexity=0.6,
                use_of_metaphors=False,
                use_of_statistics=True,
                has_intro=True,
                has_conclusion=True,
                uses_headers=False,
                paragraph_count=3,
                focuses_on_winners=True,
                focuses_on_losers=False,
                includes_predictions=True,
                includes_awards=False,
                mentions_specific_players=True,
                common_phrases=[],
                signature_words=[],
                writing_patterns={}
            ),
            generated_at=datetime.fromisoformat(row["generated_at"]),
            last_used=datetime.fromisoformat(row["last_used"]) if row.get("last_used") else None,
            usage_count=row.get("usage_count", 0),
            is_active=row.get("is_active", True),
            is_default=row.get("is_default", False)
        )


# Global instance
template_service = TemplateService()
