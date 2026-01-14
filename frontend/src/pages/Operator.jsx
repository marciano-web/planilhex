import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../lib/api.js";
import * as XLSX from "xlsx";
import Handsontable from "handsontable";
import { HotTable } from "@handsontable/react";
import { HyperFormula } from "hyperformula";
import "handsontable/dist/handsontable.full.min.css";

function hexToUint8(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.substr(i*2, 2), 16);
  }
  return bytes;
}

export default function Operator() {
  const [templates, setTemplates] = useState([]);
  const [selected, setSelected] = useState(null);
  const [mappedCells, setMappedCells] = useState([]);
  const [instance, setInstance] = useState(null);

  const [sheetData, setSheetData] = useState([[]]);
  const [sheetName, setSheetName] = useState("Sheet1");
  const [audit, setAudit] = useState([]);

  const hfRef = useRef(null);

  async function loadTemplates() {
    setTemplates(await api("/templates"));
  }
  useEffect(()=>{ loadTemplates(); }, []);

  async function openTemplate(t) {
    setSelected(t);
    const cells = await api(`/templates/${t.id}/mapped-cells`);
    setMappedCells(cells);

    const inst = await api(`/instances`, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ template_id: t.id, title: `${t.name} - preenchimento` })
    });
    setInstance(inst);

    const wbResp = await api(`/templates/${t.id}/workbook`);
    const bytes = hexToUint8(wbResp.base64);
    const workbook = XLSX.read(bytes, {type:"array"});
    const first = workbook.SheetNames[0];
    setSheetName(first);
    const ws = workbook.Sheets[first];
    const arr = XLSX.utils.sheet_to_json(ws, {header:1, blankrows:true});
    setSheetData(arr.length ? arr : [[]]);

    // HyperFormula engine
    if (!hfRef.current) {
      hfRef.current = HyperFormula.buildEmpty({ licenseKey: "gpl-v3" });
    }
  }

  const mappedSet = useMemo(()=>{
    const s = new Set();
    for (const c of mappedCells) s.add(`${c.sheet_name}:${c.cell_ref}`);
    return s;
  }, [mappedCells]);

  function cellReadOnly(row, col) {
    // Convert row/col to A1
    const cellRef = XLSX.utils.encode_cell({r: row, c: col});
    return !mappedSet.has(`${sheetName}:${cellRef}`);
  }

  function onBeforeChange(changes) {
    if (!changes) return;
    // prevent edits outside mapped cells
    const filtered = [];
    for (const ch of changes) {
      const [row, col, oldValue, newValue] = ch;
      if (cellReadOnly(row, col)) continue;
      filtered.push(ch);
    }
    changes.length = 0;
    for (const x of filtered) changes.push(x);
  }

  function onAfterChange(changes, source) {
    if (!changes || source === "loadData") return;
    const newAudit = [];
    for (const ch of changes) {
      const [row, col, oldValue, newValue] = ch;
      const cellRef = XLSX.utils.encode_cell({r: row, c: col});
      newAudit.push({
        event_type: "edit",
        sheet_name: sheetName,
        cell_ref: cellRef,
        old_value: String(oldValue ?? ""),
        new_value: String(newValue ?? ""),
        meta_json: "{}"
      });
    }
    if (newAudit.length) setAudit(prev => [...prev, ...newAudit]);
  }

  async function save() {
    if (!instance) return;
    // collect mapped values only
    const values = [];
    for (const c of mappedCells) {
      if (c.sheet_name !== sheetName) continue;
      const addr = XLSX.utils.decode_cell(c.cell_ref);
      const v = (sheetData[addr.r] && sheetData[addr.r][addr.c] != null) ? sheetData[addr.r][addr.c] : "";
      values.push({ sheet_name: sheetName, cell_ref: c.cell_ref, value: String(v) });
    }
    await api(`/instances/${instance.id}/save`, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ values, audit })
    });
    alert("Salvo com sucesso.");
    setAudit([]);
  }

  async function exportPdf() {
    if (!instance) return;
    const res = await api(`/instances/${instance.id}/export`, { method:"POST" });
    // backend returns {filename, pdf_hex}
    const bytes = hexToUint8(res.pdf_hex);
    const blob = new Blob([bytes], {type:"application/pdf"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = res.filename || "export.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <h3>Operação</h3>
      <div style={{display:"flex", gap: 16}}>
        <div style={{minWidth: 280}}>
          <p><b>Templates</b></p>
          <ul>
            {templates.map(t=>(
              <li key={t.id}>
                <button onClick={()=>openTemplate(t)}>{t.name}</button>
              </li>
            ))}
          </ul>
          {selected && (
            <>
              <hr/>
              <p><b>Template:</b> {selected.name}</p>
              <p><b>Células mapeadas:</b> {mappedCells.filter(c=>c.sheet_name===sheetName).length}</p>
              <button onClick={save} disabled={!instance}>Salvar</button>
              <button onClick={exportPdf} disabled={!instance} style={{marginLeft: 8}}>Exportar PDF</button>
              <div style={{marginTop: 10}}>
                <small>Obs.: edição bloqueada fora das células mapeadas.</small>
              </div>
              <div style={{marginTop: 10}}>
                <small>Audit pendente: {audit.length} eventos.</small>
              </div>
            </>
          )}
        </div>

        <div style={{flex: 1}}>
          {!selected ? <p>Selecione um template para carregar.</p> : (
            <div style={{border:"1px solid #ddd", borderRadius: 8, padding: 8}}>
              <HotTable
                data={sheetData}
                colHeaders={true}
                rowHeaders={true}
                height={640}
                licenseKey="non-commercial-and-evaluation"
                beforeChange={onBeforeChange}
                afterChange={onAfterChange}
                cells={(row, col)=>({ readOnly: cellReadOnly(row, col) })}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
