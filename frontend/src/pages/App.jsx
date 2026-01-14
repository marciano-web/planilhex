import React, { useEffect, useState } from "react";
import { login, setToken, api, getToken } from "../lib/api.js";
import AdminTemplates from "./AdminTemplates.jsx";
import Operator from "./Operator.jsx";

export default function App() {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function loadMe() {
    try {
      const data = await api("/me");
      setMe(data);
    } catch (e) {
      setMe(null);
    }
  }

  useEffect(() => { if (getToken()) loadMe(); }, []);

  async function onLogin(e) {
    e.preventDefault();
    setErr("");
    try {
      const t = await login(email, password);
      setToken(t.access_token);
      await loadMe();
    } catch (e) {
      setErr(e.message);
    }
  }

  if (!me) {
    return (
      <div style={{maxWidth: 420, margin: "60px auto", fontFamily: "Arial"}}>
        <h2>ExcelFlow MVP</h2>
        <p>Login</p>
        <form onSubmit={onLogin}>
          <div style={{marginBottom: 10}}>
            <label>Email</label><br/>
            <input value={email} onChange={e=>setEmail(e.target.value)} style={{width:"100%", padding:8}} />
          </div>
          <div style={{marginBottom: 10}}>
            <label>Senha</label><br/>
            <input type="password" value={password} onChange={e=>setPassword(e.target.value)} style={{width:"100%", padding:8}} />
          </div>
          <button style={{padding:"10px 14px"}}>Entrar</button>
          {err && <p style={{color:"crimson"}}>{err}</p>}
        </form>
        <hr/>
        <small>
          <b>Admin inicial</b>: definido por <code>ADMIN_EMAIL</code> / <code>ADMIN_PASSWORD</code> no backend.
        </small>
      </div>
    );
  }

  return (
    <div style={{fontFamily:"Arial", padding: 16}}>
      <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
        <h2>ExcelFlow MVP</h2>
        <div>
          <span style={{marginRight: 12}}><b>{me.email}</b> ({me.role})</span>
          <button onClick={()=>{localStorage.removeItem("token"); location.reload();}}>Sair</button>
        </div>
      </div>
      {me.role === "admin" ? <AdminTemplates /> : <Operator />}
    </div>
  );
}
