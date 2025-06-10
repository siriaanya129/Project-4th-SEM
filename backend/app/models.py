# In backend/app/models.py
from pydantic import BaseModel
from typing import List, Dict, Any

class PerformanceBreakdownPayload(BaseModel):
    performance_breakdown: List[Dict[str, Any]]