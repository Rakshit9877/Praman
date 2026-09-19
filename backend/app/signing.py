import json
from typing import Any
from pydantic import BaseModel

def canonicalize(model_or_dict: Any) -> str:
    """
    Returns the exact UTF-8 JSON string that will be signed.
    This must match the browser's JSON.stringify format exactly.
    """
    if isinstance(model_or_dict, BaseModel):
        data = model_or_dict.model_dump(mode="json")
    elif isinstance(model_or_dict, dict):
        data = model_or_dict
    else:
        raise ValueError("Must be a Pydantic model or a dictionary")
        
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
