from pydantic import BaseModel, Field
from typing import Dict, List, Any

class VisitCount(BaseModel):
    page_id: str
    visits: int
    served_via: str
