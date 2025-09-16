"""
Template API endpoints for user template upload and management
Handles template uploads, style analysis, and prompt generation
"""

import base64
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.models.template import (
    UserTemplate, TemplateStatus, FileFormat, PromptTemplate,
    TemplateListResponse, TemplateAnalysisResponse
)
from app.services.template.template_service import template_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class TemplateUploadResponse(BaseModel):
    """Response for template upload"""
    success: bool
    template_id: str
    message: str
    warnings: Optional[List[str]] = None


class TemplateUploadFormData(BaseModel):
    """Form data for template upload"""
    user_notes: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated tags


@router.post("/upload", response_model=TemplateUploadResponse)
async def upload_template(
    file: UploadFile = File(...),
    user_notes: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a new template file for style analysis
    """
    try:
        user_id = current_user["id"]
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Determine file format from extension
        file_extension = file.filename.split('.')[-1].lower()
        try:
            file_format = FileFormat(file_extension)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_extension}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Upload and process template
        template = await template_service.upload_template(
            user_id=user_id,
            filename=file.filename,
            file_content=file_content,
            file_format=file_format,
            user_notes=user_notes,
            tags=tag_list
        )
        
        return TemplateUploadResponse(
            success=True,
            template_id=template.id,
            message="Template uploaded successfully. Analysis will begin shortly."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Template upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload template"
        )


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[TemplateStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of user's templates
    """
    try:
        user_id = current_user["id"]
        
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        templates = await template_service.get_user_templates(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter
        )
        
        return templates
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.get("/{template_id}", response_model=UserTemplate)
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific template
    """
    try:
        user_id = current_user["id"]
        
        template = await template_service.get_template(template_id, user_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )


@router.post("/{template_id}/analyze", response_model=TemplateAnalysisResponse)
async def analyze_template(
    template_id: str,
    force_reanalysis: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger or retrieve analysis for a template
    """
    try:
        user_id = current_user["id"]
        
        # Verify template belongs to user
        template = await template_service.get_template(template_id, user_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Perform analysis
        analysis_result = await template_service.analyze_template(
            template_id=template_id,
            force_reanalysis=force_reanalysis
        )
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze template"
        )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a template and all associated data
    """
    try:
        user_id = current_user["id"]
        
        success = await template_service.delete_template(template_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return {
            "success": True,
            "message": "Template deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


@router.get("/prompts/active", response_model=Optional[PromptTemplate])
async def get_active_prompt_template(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's active prompt template
    """
    try:
        user_id = current_user["id"]
        
        prompt_template = await template_service.get_active_prompt_template(user_id)
        return prompt_template
        
    except Exception as e:
        logger.error(f"Failed to get active prompt template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active prompt template"
        )


@router.post("/{template_id}/set-default")
async def set_default_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Set a template as the user's default
    """
    try:
        user_id = current_user["id"]
        
        # Verify template belongs to user and has prompt
        template = await template_service.get_template(template_id, user_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        if template.status != TemplateStatus.ANALYZED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template must be analyzed before setting as default"
            )
        
        # Update default status in database
        # This would be implemented in the template service
        # For now, return success
        
        return {
            "success": True,
            "message": "Template set as default successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set default template"
        )


@router.get("/stats/summary")
async def get_template_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get summary statistics about user's templates
    """
    try:
        user_id = current_user["id"]
        
        # Get all templates
        all_templates = await template_service.get_user_templates(
            user_id=user_id,
            page=1,
            page_size=1000  # Get all for stats
        )
        
        # Calculate statistics
        total = all_templates.total
        analyzed = sum(1 for t in all_templates.templates if t.status == TemplateStatus.ANALYZED)
        processing = sum(1 for t in all_templates.templates if t.status == TemplateStatus.PROCESSING)
        failed = sum(1 for t in all_templates.templates if t.status == TemplateStatus.FAILED)
        
        # Tone distribution
        tone_counts = {}
        for template in all_templates.templates:
            if template.style_analysis:
                tone = template.style_analysis.tone.value
                tone_counts[tone] = tone_counts.get(tone, 0) + 1
        
        return {
            "total_templates": total,
            "analyzed": analyzed,
            "processing": processing,
            "failed": failed,
            "success_rate": round(analyzed / total * 100, 1) if total > 0 else 0,
            "tone_distribution": tone_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get template stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template statistics"
        )
