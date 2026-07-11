"use client";
import { useState } from "react";

const CATS = ["mixer", "cartridge", "valve", "aerator", "handle", "spindle", "washer/seal", "shower slide", "shower head", "shower rail", "hand shower", "waste", "toilet seat", "toilet valve", "diverter", "other"];

export default function Admin() {
  const [pw, setPw] = useState("");
  const [f, setF] = useState({ url: "", category: "mixer", brand: "", model: "", part_no: "", size: "", fits: "", buy_url: "", confirm: false });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [added, setAdded] = useState([]);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  async function submit(e) {
    e.preventDefault();
    if (!pw) { setMsg({ err: "Enter the admin password first." }); return; }
    if (!f.url || !f.model) { setMsg({ err: "Paste a link and enter at least a model name." }); return; }
    setBusy(true); setMsg(null);
    try {
      const r = await fetch("/api/ingest", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ ...f, password: pw }) });
      const j = await r.json();
      if (!r.ok) { setMsg({ err: j.error || "Failed" }); }
      else { setMsg({ ok: `Added #${j.product.id}: ${j.product.brand || ""} ${j.product.model}` }); setAdded([j.product, ...added].slice(0, 12)); setF({ ...f, url: "", model: "", part_no: "", size: "", fits: "", buy_url: "" }); }
    } catch { setMsg({ err: "Network error" }); }
    setBusy(false);
  }

  return (
    <main className="container" style={{ maxWidth: 720, padding: "28px 18px 64px" }}>
      <h1 style={{ marginBottom: 4 }}>Add a product</h1>
      <p className="sub" style={{ color: "#5b6875", marginTop: 0 }}>Paste a product link — TapSnap grabs the photo, fingerprints it, and adds it to the live catalogue instantly. No redeploy.</p>

      <form onSubmit={submit} style={{ display: "grid", gap: 12, marginTop: 18 }}>
        <input className="brandfilter" type="password" placeholder="Admin password" value={pw} onChange={(e) => setPw(e.target.value)} style={{ margin: 0 }} />
        <input className="brandfilter" placeholder="Product link (page or image URL) *" value={f.url} onChange={set("url")} style={{ margin: 0 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <select className="brandfilter" value={f.category} onChange={set("category")} style={{ margin: 0 }}>{CATS.map((c) => <option key={c} value={c}>{c}</option>)}</select>
          <input className="brandfilter" placeholder="Brand" value={f.brand} onChange={set("brand")} style={{ margin: 0 }} />
        </div>
        <input className="brandfilter" placeholder="Model / name *" value={f.model} onChange={set("model")} style={{ margin: 0 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <input className="brandfilter" placeholder="Part no / cartridge code" value={f.part_no} onChange={set("part_no")} style={{ margin: 0 }} />
          <input className="brandfilter" placeholder="Size (e.g. 35mm)" value={f.size} onChange={set("size")} style={{ margin: 0 }} />
        </div>
        <input className="brandfilter" placeholder="Fits / notes (optional)" value={f.fits} onChange={set("fits")} style={{ margin: 0 }} />
        <input className="brandfilter" placeholder="Buy link (optional — defaults to the pasted link)" value={f.buy_url} onChange={set("buy_url")} style={{ margin: 0 }} />
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14, color: "#5b6875" }}>
          <input type="checkbox" checked={f.confirm} onChange={set("confirm")} /> Flag &ldquo;confirm size/fit before ordering&rdquo;
        </label>
        <button className="btn btn-primary" disabled={busy} style={{ justifyContent: "center" }}>{busy ? "Adding…" : "Add to catalogue"}</button>
      </form>

      {msg && <div className={"aibar " + (msg.err ? "muted" : "")} style={{ marginTop: 16, color: msg.err ? "#b4413c" : undefined }}>{msg.err || msg.ok}</div>}

      {added.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 16 }}>Added this session</h2>
          <div className="models" style={{ marginTop: 10 }}>
            {added.map((p) => (
              <div className="modelcard" key={p.id}>
                <div className="mimg">{p.photo_url ? <img src={p.photo_url} alt={p.model} loading="lazy" /> : <span className="mph">no photo</span>}</div>
                <div className="minfo"><div className="mname">{p.brand} {p.model}</div><div className="mhint">{p.category}{p.part_no ? " · " + p.part_no : ""}</div></div>
              </div>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}
