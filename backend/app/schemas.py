from pydantic import BaseModel
from typing import List, Optional

class LoginReq(BaseModel):
    email: str
    password: str

class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResp(BaseModel):
    id: int
    email: str
    role: str

class TemplateResp(BaseModel):
    id: int
    name: str
    original_filename: str

class MapCell(BaseModel):
    sheet_name: str = "Sheet1"
    cell_ref: str
    label: str = ""
    data_type: str = "text"

class TemplateMapReq(BaseModel):
    cells: List[MapCell]

class InstanceCreateReq(BaseModel):
    template_id: int
    title: str = ""

class InstanceResp(BaseModel):
    id: int
    template_id: int
    title: str

class ValueItem(BaseModel):
    sheet_name: str = "Sheet1"
    cell_ref: str
    value: str

class AuditItem(BaseModel):
    event_type: str = "edit"
    sheet_name: str = ""
    cell_ref: str = ""
    old_value: str = ""
    new_value: str = ""
    meta_json: str = "{}"

class InstanceSaveReq(BaseModel):
    values: List[ValueItem]
    audit: List[AuditItem] = []

class ExportResp(BaseModel):
    filename: str
