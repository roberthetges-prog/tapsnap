import models from "../../../lib/models.json";
import parts from "../../../lib/parts.json";
import cartimg from "../../../lib/cartimg.json";
import embeddings from "../../../lib/embeddings.json";
import { sbAdmin } from "../../../lib/supabase.js";

export const runtime = "nodejs";
export const maxDuration = 120;

function decodeVec(b64) {
  const bin = Buffer.from(b64, "base64");
  const out = new Array(bin.length);
  for (let i = 0; i < bin.length; i++) { let v = bin[i]; if (v > 127) v -= 256; out[i] = Math.round((v / 127) * 1e5) / 1e5; }
  return "[" + out.join(",") + "]";
}

function buildRows() {
  const embByKey = {};
  for (const e of embeddings) embByKey[e.k] = e;
  const rows = [];
  for (const m of models) {
    if (!m.photo) continue;
    const k = m.brand + "|" + m.model; const e = embByKey[k];
    rows.push({ brand: m.brand, model: m.model, category: "mixer", size: m.size || null, part_no: m.cartPart || null, fits: null, photo_url: m.photo, buy_url: m.buyUrl || null, confirm: !!m.confirm, exploded: m.exploded || null, source_key: k, embedding: e ? decodeVec(e.v) : null });
  }
  for (const p of parts) {
    if (!p.photo) continue;
    const k = "P|" + p.id; const e = embByKey[k];
    const cat = String(p.category || p.productType || "part").toLowerCase();
    rows.push({ brand: p.brand || null, model: p.name || p.component || p.range || String(p.id), category: cat, size: p.size || p.dimension || null, part_no: p.partNumber || p.cartPart || null, fits: p.range || null, photo_url: p.photo, buy_url: p.buyUrl || null, confirm: false, exploded: null, source_key: k, embedding: e ? decodeVec(e.v) : null });
  }
  const byCode = (cartimg && cartimg.byCode) || {};
  for (const code of Object.keys(byCode)) {
    const k = "C|" + code; const e = embByKey[k];
    rows.push({ brand: null, model: code + " cartridge", category: "cartridge", size: null, part_no: code, fits: null, photo_url: byCode[code], buy_url: null, confirm: true, exploded: null, source_key: k, embedding: e ? decodeVec(e.v) : null });
  }
  return rows;
}

export async function GET(request) {
  const url = new URL(request.url);
  const admin = (process.env.EMBED_TOKEN || "").trim();
  if (!admin || (url.searchParams.get("key") || "").trim() !== admin) return Response.json({ error: "forbidden" }, { status: 403 });
  if (url.searchParams.get("go") !== "migrate-tapsnap-once") return Response.json({ error: "add ?go=migrate-tapsnap-once" }, { status: 400 });
  const sb = sbAdmin();
  if (!sb) return Response.json({ error: "supabase admin not configured (need SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY)" }, { status: 500 });
  const rows = buildRows();
  let done = 0; const errors = [];
  for (let i = 0; i < rows.length; i += 100) {
    const batch = rows.slice(i, i + 100);
    const { error } = await sb.from("products").upsert(batch, { onConflict: "source_key" });
    if (error) errors.push({ at: i, msg: error.message }); else done += batch.length;
  }
  const { count } = await sb.from("products").select("*", { count: "exact", head: true });
  return Response.json({ built: rows.length, upserted: done, tableCount: count, errors });
}
