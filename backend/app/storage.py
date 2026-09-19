import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "backend/data/uploads"))

def init_storage():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile, prefix: str = "") -> str:
    """Saves an uploaded file and returns its absolute path."""
    init_storage()
    ext = Path(upload_file.filename).suffix if upload_file.filename else ""
    file_id = f"{prefix}{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / file_id
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return str(file_path.absolute())

def get_file_path(file_id: str) -> str:
    return str((UPLOAD_DIR / file_id).absolute())
