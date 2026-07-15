"use client";
import { useState } from "react";

const CATS = ["mixer", "cartridge", "valve", "aerator", "handle", "spindle", "washer/seal", "shower slide", "shower head", "shower rail", "hand shower", "waste", "toilet seat", "toilet valve", "diverter", "other"];

export default function Admin() {
  const [pw, setPw] = useState("");
  const [f, setF] = useState({ url: "", category: "mixer", brand: "", model: "", part_no: "", size: "", fits: "", buy_url: "", confirm: false });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [added, setAdded] = useState([]);
  const [bfBusy, setBfBusy] = useState(false);
  const [bf, setBf] = useState(null);
  const [bbBusy, setBbBusy] = useState(false);
  const [bb, setBb] = useState(null);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  // Some retailer CDNs (Mitre 10's, for one) serve a real browser but block our server's IP.
  // Those images can never be fingerprinted the normal way. So: load the picture HERE, in the
  // browser the CDN trusts, shrink it, and post the pixels to be fingerprinted.
  async function toB64(url) {
    const img = await new Promise((res) => {
      const i = new Image();
      i.crossOrigin = "anonymous";
      i.onload = () => res(i);
      i.onerror = () => res(null);
      i.src = url;
    });
    if (!img || !img.naturalWidth) return null;
    const side = Math.max(img.naturalWidth, img.naturalHeight);
    const scale = Math.min(1, 512 / side);
    const cv = document.createElement("canvas");
    cv.width = Math.round(img.naturalWidth * scale);
    cv.height = Math.round(img.naturalHeight * scale);
    const cx = cv.getContext("2d");
    cx.fillStyle = "#ffffff";
    cx.fillRect(0, 0, cv.width, cv.height);
    cx.drawImage(img, 0, 0, cv.width, cv.height);
    try { return cv.toDataURL("image/jpeg", 0.9); } catch { return null; } // tainted canvas = no CORS
  }

  async function browserBackfill() {
    if (!pw) { setBb({ err: "Enter the admin password first." }); return; }
    setBbBusy(true); setBb(null);
    try {
      const lr = await fetch("/api/embed-image?list=1");
      const lj = await lr.json();
      const list = (lj && lj.items) || [];
      if (!list.length) { setBb({ ok: "Nothing left — every photo has a fingerprint." }); setBbBusy(false); return; }
      const items = [];
      const failed = [];
      for (const p of list) {
        const d = await toB64(p.photo_url);
        if (d) items.push({ id: p.id, data: d });
        else failed.push(`${p.brand} ${p.model}`);
      }
      if (!items.length) {
        setBb({ err: `Your browser couldn't load any of those ${list.length} images either — they may be genuinely gone.` });
        setBbBusy(false); return;
      }
      const r = await fetch("/api/embed-image", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ password: pw, items }) });
      const j = await r.json();
      if (!r.ok) setBb({ err: j.error || "Failed" });
      else setBb({ ok: `Fingerprinted ${j.embedded} image${j.embedded === 1 ? "" : "s"} through your browser. ${j.remaining} still without a fingerprint.`, failed });
    } catch { setBb({ err: "Network error" }); }
    setBbBusy(false);
  }

  async function backfill() {
    if (!pw) { setBf({ err: "Enter the admin password first." }); return; }
    setBfBusy(true); setBf(null);
    try {
      const r = await fetch("/api/embed-backfill", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ password: pw, limit: 40 }) });
      const j = await r.json();
      if (!r.ok) setBf({ err: j.error || "Failed" });
      else setBf({ ok: `Fingerprinted ${j.embedded} image${j.embedded === 1 ? "" : "s"}. ${j.remaining} still without a photo fingerprint.`, errors: (j.errors || []).length });
    } catch { setBf({ err: "Network error" }); }
    setBfBusy(false);
  }

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

      <div style={{ marginTop: 28, paddingTop: 20, borderTop: "1px solid #e3e8ee" }}>
        <h2 style={{ fontSize: 16, marginBottom: 4 }}>Maintenance</h2>
        <p className="sub" style={{ color: "#5b6875", marginTop: 0, fontSize: 14 }}>Fingerprint any catalogue products that are missing a photo match (runs up to 40 at a time — click again if more remain).</p>
        <button type="button" className="btn" onClick={backfill} disabled={bfBusy} style={{ justifyContent: "center" }}>{bfBusy ? "Fingerprinting…" : "Fingerprint missing images"}</button>
        {bf && <div className={"aibar " + (bf.err ? "muted" : "")} style={{ marginTop: 12, color: bf.err ? "#b4413c" : undefined }}>{bf.err || bf.ok}{bf.errors ? ` (${bf.errors} couldn’t be fetched)` : ""}</div>}

        <p className="sub" style={{ color: "#5b6875", marginTop: 20, marginBottom: 6, fontSize: 14 }}>
          Some retailers (Mitre 10 for one) serve pictures to a normal browser but block our server, so those
          products can never be fingerprinted the usual way. This loads them here, in your browser, and sends
          the pixels over. Use it for whatever the button above reports as &ldquo;couldn&rsquo;t be fetched&rdquo;.
        </p>
        <button type="button" className="btn" onClick={browserBackfill} disabled={bbBusy} style={{ justifyContent: "center" }}>{bbBusy ? "Fetching in your browser…" : "Fingerprint the blocked ones via my browser"}</button>
        {bb && (
          <div className={"aibar " + (bb.err ? "muted" : "")} style={{ marginTop: 12, color: bb.err ? "#b4413c" : undefined }}>
            {bb.err || bb.ok}
            {bb.failed && bb.failed.length ? <div style={{ marginTop: 6, fontSize: 13 }}>Your browser couldn&rsquo;t load: {bb.failed.join(", ")}</div> : null}
          </div>
        )}
      </div>

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
