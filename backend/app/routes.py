from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .db import get_db
from .config import settings
from .models import User, Template, TemplateCell, Instance, InstanceValue, AuditEvent
from .security import verify_password, create_access_token
from .deps import get_current_user, require_admin
from .schemas import (
    LoginReq, TokenResp, MeResp,
    TemplateResp, TemplateMapReq,
    InstanceCreateReq, InstanceResp,
    InstanceSaveReq, ExportResp
)
from datetime import datetime
import json
from .spreadsheet import convert_to_xlsx, fill_values, xlsx_to_pdf, build_audit_pdf, merge_pdf_with_audit

router = APIRouter()

@router.post("/auth/login", response_model=TokenResp)
def login(payload: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active == True).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.email, settings.jwt_secret)
    return TokenResp(access_token=token)

@router.get("/me", response_model=MeResp)
def me(user: User = Depends(get_current_user)):
    return MeResp(id=user.id, email=user.email, role=user.role)

@router.post("/templates", response_model=TemplateResp)
def upload_template(
    name: str,
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    raw = file.file.read()
    # Convert ods->xlsx for consistent downstream handling
    xlsx_bytes, mime = convert_to_xlsx(raw, file.filename or "template.xlsx")
    tpl = Template(
        name=name,
        original_filename=(file.filename or "template.xlsx"),
        mime_type=mime,
        file_bytes=xlsx_bytes,
        created_by=admin.id,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return TemplateResp(id=tpl.id, name=tpl.name, original_filename=tpl.original_filename)

@router.post("/templates/{template_id}/map")
def map_cells(
    template_id: int,
    payload: TemplateMapReq,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tpl = db.query(Template).filter(Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    # Replace mapping for simplicity
    db.query(TemplateCell).filter(TemplateCell.template_id == template_id).delete()
    for c in payload.cells:
        db.add(TemplateCell(
            template_id=template_id,
            sheet_name=c.sheet_name,
            cell_ref=c.cell_ref.upper(),
            label=c.label,
            data_type=c.data_type,
        ))
    db.commit()
    return {"ok": True, "count": len(payload.cells)}

@router.get("/templates")
def list_templates(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Template).order_by(Template.created_at.desc()).all()
    return [{"id": t.id, "name": t.name, "original_filename": t.original_filename} for t in rows]

@router.get("/templates/{template_id}/mapped-cells")
def get_mapped_cells(template_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cells = db.query(TemplateCell).filter(TemplateCell.template_id == template_id).all()
    return [{"sheet_name": c.sheet_name, "cell_ref": c.cell_ref, "label": c.label, "data_type": c.data_type} for c in cells]

@router.get("/templates/{template_id}/workbook")
def download_template(template_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tpl = db.query(Template).filter(Template.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return {
        "filename": f"template-{template_id}.xlsx",
        "mime": tpl.mime_type,
        "base64": tpl.file_bytes.hex()  # frontend will fetch as hex and convert to bytes
    }

@router.post("/instances", response_model=InstanceResp)
def create_instance(
    payload: InstanceCreateReq,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tpl = db.query(Template).filter(Template.id == payload.template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    inst = Instance(template_id=payload.template_id, created_by=user.id, title=payload.title)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    db.add(AuditEvent(instance_id=inst.id, user_id=user.id, event_type="create", meta_json=json.dumps({"template_id": payload.template_id})))
    db.commit()
    return InstanceResp(id=inst.id, template_id=inst.template_id, title=inst.title)

@router.get("/instances/{instance_id}")
def get_instance(instance_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    values = db.query(InstanceValue).filter(InstanceValue.instance_id == instance_id).all()
    audit = db.query(AuditEvent).filter(AuditEvent.instance_id == instance_id).order_by(AuditEvent.created_at.asc()).all()
    return {
        "id": inst.id,
        "template_id": inst.template_id,
        "title": inst.title,
        "values": [{"sheet_name": v.sheet_name, "cell_ref": v.cell_ref, "value": v.value} for v in values],
        "audit": [{
            "event_type": a.event_type, "sheet_name": a.sheet_name, "cell_ref": a.cell_ref,
            "old_value": a.old_value, "new_value": a.new_value, "created_at": a.created_at.isoformat()+"Z",
            "meta_json": a.meta_json
        } for a in audit]
    }

@router.post("/instances/{instance_id}/save")
def save_instance(
    instance_id: int,
    payload: InstanceSaveReq,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    # upsert values
    for item in payload.values:
        sheet = item.sheet_name
        cell = item.cell_ref.upper()
        existing = db.query(InstanceValue).filter(
            InstanceValue.instance_id == instance_id,
            InstanceValue.sheet_name == sheet,
            InstanceValue.cell_ref == cell
        ).first()
        if existing:
            existing.value = item.value
        else:
            db.add(InstanceValue(instance_id=instance_id, sheet_name=sheet, cell_ref=cell, value=item.value))

    # audit
    for a in payload.audit:
        db.add(AuditEvent(
            instance_id=instance_id,
            user_id=user.id,
            event_type=a.event_type,
            sheet_name=a.sheet_name,
            cell_ref=a.cell_ref,
            old_value=a.old_value,
            new_value=a.new_value,
            meta_json=a.meta_json or "{}",
        ))
    db.add(AuditEvent(instance_id=instance_id, user_id=user.id, event_type="save", meta_json=json.dumps({"values_count": len(payload.values)})))
    db.commit()
    return {"ok": True}

@router.post("/instances/{instance_id}/export", response_model=ExportResp)
def export_pdf(
    instance_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    tpl = db.query(Template).filter(Template.id == inst.template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    values = db.query(InstanceValue).filter(InstanceValue.instance_id == instance_id).all()
    filled_xlsx = fill_values(tpl.file_bytes, [{"sheet_name": v.sheet_name, "cell_ref": v.cell_ref, "value": v.value} for v in values])

    main_pdf = xlsx_to_pdf(filled_xlsx)

    # Build audit table (include user email)
    audits = db.query(AuditEvent, User).join(User, User.id == AuditEvent.user_id)        .filter(AuditEvent.instance_id == instance_id)        .order_by(AuditEvent.created_at.asc()).all()

    audit_rows = [{
        "created_at": ae.created_at.isoformat()+"Z",
        "user_email": u.email,
        "event_type": ae.event_type,
        "sheet_name": ae.sheet_name,
        "cell_ref": ae.cell_ref,
        "old_value": ae.old_value,
        "new_value": ae.new_value,
    } for ae, u in audits if ae.event_type in ("edit","save","export","create")]

    audit_pdf = build_audit_pdf(audit_rows)
    out_pdf = merge_pdf_with_audit(main_pdf, audit_pdf)

    # store an export audit event
    db.add(AuditEvent(instance_id=instance_id, user_id=user.id, event_type="export"))
    db.commit()

    # Return as hex (MVP). Frontend will download.
    filename = f"instance-{instance_id}.pdf"
    return {"filename": filename, "pdf_hex": out_pdf.hex()}
