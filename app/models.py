from typing import Optional
import uuid
from pydantic import BaseModel, Field

class FileModel(BaseModel):
    id:str = Field(default_factory=uuid.uuid4, alias="_id")
    title: str
    description: str

class FileUpdateModel(BaseModel):
    title: Optional[str]
    description: Optional[str]
