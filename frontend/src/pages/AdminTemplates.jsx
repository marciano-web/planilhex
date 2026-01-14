import React, { useEffect, useState } from "react";
import { api } from "../lib/api.js";

export default function AdminTemplates() {
  const [templates, setTemplates] = useState([]);
  const [name, setName] = useState("");
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");
  const [selected, setSelected] = useState(null);
  const [mapped, setMapped] = useState([]);
  const [cellInput, setCellInput] = useState("A1");
  const [sheetName, setSheetName] = useState("Sheet1");
  const [label, setLabel] = useState("");

  async function load() {
    const t = await api("/templates");
    setTemplates(t);
  }
  useEffect(()=>{ load(); }, []);

  async function upload(e) {
    e.preventDefault();
    setMsg("");
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${import.meta.env.VITE_API_URL}/templates?name=${encodeURIComponent(name)}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
      body: fd
    });
    if (!res.ok) {
      setMsg("Erro ao enviar template");
      return;
    }
    setMsg("Template enviado!");
    setName(""); setFile(null);
    await load();
  }

  async function selectTemplate(t) {
    setSelected(t);
    const cells = await api(`/templates/${t.id}/mapped-cells`);
    setMapped(cells);
  }

  function addCell() {
    const c = { sheet_name: sheetName, cell_ref: cellInput.toUpperCase(), label, data_type: "text" };
    setMapped(prev => {
      const exists = prev.some(x => x.sheet_name===c.sheet_name && x.cell_ref===c.cell_ref);
      if (exists) return prev;
      return [...prev, c];
    });
    setLabel("");
  }

  async function saveMap() {
    await api(`/templates/${selected.id}/map`, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ cells: mapped })
    });
    setMsg("Mapeamento salvo!");
  }

  return (
    <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap: 18}}>
      <div style={{border:"1px solid #ddd", padding: 12, borderRadius: 8}}>
        <h3>Upload de Template</h3>
        <form onSubmit={upload}>
          <div style={{marginBottom:10}}>
            <label>Nome do template</label><br/>
            <input value={name} onChange={e=>setName(e.target.value)} style={{width:"100%", padding:8}} />
          </div>
          <div style={{marginBottom:10}}>
            <label>Arquivo (.xlsx ou .ods)</label><br/>
            <input type="file" accept=".xlsx,.ods" onChange={e=>setFile(e.target.files[0])} />
          </div>
          <button disabled={!name || !file}>Enviar</button>
        </form>
        {msg && <p>{msg}</p>}
        <hr/>
        <h3>Templates</h3>
        <ul>
          {templates.map(t => (
            <li key={t.id}>
              <button onClick={()=>selectTemplate(t)}>{t.name}</button>
              <small style={{marginLeft:8, color:"#666"}}>({t.original_filename})</small>
            </li>
          ))}
        </ul>
      </div>

      <div style={{border:"1px solid #ddd", padding: 12, borderRadius: 8}}>
        <h3>Mapeamento</h3>
        {!selected ? <p>Selecione um template.</p> : (
          <>
            <p><b>Template:</b> {selected.name}</p>
            <div style={{display:"flex", gap: 8, marginBottom: 10, alignItems:"end"}}>
              <div>
                <label>Aba</label><br/>
                <input value={sheetName} onChange={e=>setSheetName(e.target.value)} style={{padding:8, width:140}} />
              </div>
              <div>
                <label>Célula</label><br/>
                <input value={cellInput} onChange={e=>setCellInput(e.target.value)} style={{padding:8, width:90}} />
              </div>
              <div style={{flex:1}}>
                <label>Rótulo (opcional)</label><br/>
                <input value={label} onChange={e=>setLabel(e.target.value)} style={{padding:8, width:"100%"}} />
              </div>
              <button onClick={addCell}>Adicionar</button>
            </div>

            <div style={{maxHeight: 240, overflow:"auto", border:"1px solid #eee", padding: 8}}>
              {mapped.length === 0 ? <p>Nenhuma célula mapeada.</p> : (
                <table style={{width:"100%", fontSize: 12}}>
                  <thead><tr><th>Aba</th><th>Célula</th><th>Rótulo</th><th></th></tr></thead>
                  <tbody>
                    {mapped.map((c, idx)=>(
                      <tr key={idx}>
                        <td>{c.sheet_name}</td>
                        <td>{c.cell_ref}</td>
                        <td>{c.label}</td>
                        <td><button onClick={()=>setMapped(prev=>prev.filter((_,i)=>i!==idx))}>Remover</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div style={{marginTop: 10}}>
              <button onClick={saveMap} disabled={mapped.length===0}>Salvar mapeamento</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
