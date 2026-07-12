// Re-host images we don't control.
//
// Some suppliers (hotwatercylinders.nz is the worst offender) allow our SERVER to fetch an
// image but block it when a USER'S browser loads it from tapsnap - "hotlink protection".
// The result: the fingerprint works, but the plumber sees a broken image. Others block the
// server instead. Either way we're at the mercy of someone else's web server.
//
// This copies the image into our own Supabase Storage bucket once, and repoints the product
// at our copy. After that it always displays and can never be blocked.

import { sbAdmin } from "../../../lib/supabase.js";

export const runtime = "nodejs";
export const maxDuration = 120;

const BUCKET = "product-images";

// Hosts known to serve our server but block a user's browser (or vice-versa).
const REHOST_HOSTS = ["hotwatercylinders.nz"];

async function fetchImage(url) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15000);
  try {
    // send a same-site referer: this is what defeats their hotlink check
    let ref = "";
    try { ref = new URL(url).origin + "/"; } catch {}
    const r = await fetch(url, {
      signal: ctrl.signal,
      headers: {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "referer": ref,
      },
    });
    clearTimeout(t);
    if (!r.ok) return null;
    const ct = (r.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
    const buf = Buffer.from(await r.arrayBuffer());
    if (!buf.length) return null;
    return { buf, contentType: /^image\//.test(ct) ? ct : "image/jpeg" };
  } catch { clearTimeout(t); return null; }
}

function extFor(ct) {
  if (ct === "image/png") return "png";
  if (ct === "image/webp") return "webp";
  return "jpg";
}

export async function POST(request) {
  let body; try { body = await request.json(); } catch { return Response.json({ error: "bad request" }, { status: 400 }); }
  const admin = (process.env.ADMIN_PASSWORD || "").trim();
  if (!admin || (body && body.password) !== admin) return Response.json({ error: "forbidden" }, { status: 403 });

  const sb = sbAdmin();
  if (!sb) return Response.json({ error: "db not configured" }, { status: 500 });

  const { data: rows, error } = await sb
    .from("products")
    .select("id,photo_url")
    .not("photo_url", "is", null)
    .limit(500);
  if (error) return Response.json({ error: error.message }, { status: 500 });

  const targets = (rows || []).filter((r) =>
    REHOST_HOSTS.some((h) => String(r.photo_url).includes(h))
  ).slice(0, 30);

  let done = 0;
  const failed = [];

  for (const row of targets) {
    const img = await fetchImage(row.photo_url);
    if (!img) { failed.push({ id: row.id, e: "fetch" }); continue; }

    const path = "p/" + row.id + "." + extFor(img.contentType);
    const up = await sb.storage.from(BUCKET).upload(path, img.buf, {
      contentType: img.contentType,
      upsert: true,
    });
    if (up.error) { failed.push({ id: row.id, e: up.error.message }); continue; }

    const { data: pub } = sb.storage.from(BUCKET).getPublicUrl(path);
    const publicUrl = pub && pub.publicUrl;
    if (!publicUrl) { failed.push({ id: row.id, e: "no public url" }); continue; }

    // repoint the product at our own copy; keep the fingerprint (same picture)
    const { error: uerr } = await sb.from("products").update({ photo_url: publicUrl }).eq("id", row.id);
    if (uerr) { failed.push({ id: row.id, e: uerr.message }); continue; }
    done++;
  }

  const { count: remaining } = await sb
    .from("products")
    .select("*", { count: "exact", head: true })
    .like("photo_url", "%hotwatercylinders%");

  return Response.json({ found: targets.length, rehosted: done, remaining, failed });
}
