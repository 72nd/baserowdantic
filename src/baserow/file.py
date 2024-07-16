from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileThumbnail(BaseModel):
    """
    Data model for thumbnails. These are used in the `field.File` model.
    """
    url: str
    width: Optional[int]
    height: Optional[int]


class File(BaseModel):
    """A single file with its metadata stored in Baserow."""
    url: Optional[str] = None
    mime_type: Optional[str]
    thumbnails: Optional[dict[str, FileThumbnail]] = None
    name: str
    size: Optional[int] = None
    is_image: Optional[bool] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    original_name: Optional[str] = None
