"""
Reports Models

Pydantic models for report generation

Source:
- backend/models.py (HTMLReportRequest, PDFReportRequest)

Date created: 2025-10-14
"""

from pydantic import BaseModel
from typing import List, Optional


class HTMLReportRequest(BaseModel):
    """
    Request model for HTML report generation

    Source: backend/models.py
    """
    # New calculation selection system
    selected_calculations: List[str] = []  # IDs of calculations to include

    # Legacy fields (for compatibility)
    include_vedic: bool = True
    include_charts: bool = True
    include_compatibility: bool = False
    partner_birth_date: Optional[str] = None
    theme: str = "default"  # "default", "dark", "print"


class PDFReportRequest(BaseModel):
    """
    Request model for PDF report generation

    Source: backend/models.py
    """
    selected_calculations: List[str] = []  # IDs of calculations to include
    include_vedic: bool = True
    include_charts: bool = True
    include_compatibility: bool = False
    partner_birth_date: Optional[str] = None


__all__ = ['HTMLReportRequest', 'PDFReportRequest']
