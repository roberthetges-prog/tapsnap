// Toilet parts lookup.
// Given an identified toilet suite (id) and the user's answer to "where does the water enter
// the cistern?" (bottom | back | side), return the parts that actually fit:
//   - replacement SEAT   (matched on brand + range name, since seats state what they fit)
//   - INLET valve        (filtered by the inlet position the USER told us - we cannot see it)
//   - OUTLET valve       (brand + universal)
//   - FLUSH button/plate (brand + universal)
//
// Why we ask: bottom-inlet and back-inlet cisterns look identical from the front. The photo
// genuinely cannot tell us, so guessing would send someone home with the wrong valve.

import { sbAdmin, sbRead } from "../../../lib/supabase.js";

export const runtime = "nodejs";
export const maxDuration = 20;

// The user picks one of three. NZ suppliers also use "top" - a top-entry valve feeds in from
// above rather than underneath or behind, so it sits with "side" from the user's point of view.
const INLET_SYNONYMS = {
  bottom: ["bottom"],
  back: ["back", "rear"],
  side: ["side", "top"],
};

const UNIVERSAL = ["universal", "multi-brand", "most modern"];

function firstWords(s, n) {
  return String(s || "").split(/[\s(,\-\/]+/).filter(Boolean).slice(0, n || 2);
}

function card(row) {
  return {
    id: row.id,
    brand: row.brand || "",
    model: row.model,
    category: row.category,
    partNo: row.part_no || "",
    note: row.size || "",
    fits: row.fits || "",
    photo: row.photo_url,
    buyUrl: row.buy_url || "",
  };
}

export async function GET(request) {
  const url = new URL(request.url);
  const suiteId = parseInt(url.searchParams.get("suite") || "", 10);
  const inlet = String(url.searchParams.get("inlet") || "").toLowerCase().trim();
  if (!suiteId) return Response.json({ error: "missing suite" }, { status: 400 });

  const sb = sbAdmin() || sbRead();
  if (!sb) return Response.json({ error: "db not configured" }, { status: 500 });

  const { data: suiteRows, error: e1 } = await sb.from("products").select("*").eq("id", suiteId).limit(1);
  if (e1) return Response.json({ error: e1.message }, { status: 500 });
  const suite = suiteRows && suiteRows[0];
  if (!suite) return Response.json({ error: "suite not found" }, { status: 404 });

  const { data: all, error: e2 } = await sb
    .from("products")
    .select("id,brand,model,category,part_no,size,fits,photo_url,buy_url")
    .in("category", ["toilet seat", "toilet inlet valve", "toilet outlet valve", "flush button"])
    .eq("active", true);
  if (e2) return Response.json({ error: e2.message }, { status: 500 });

  const brand = String(suite.brand || "").toLowerCase();
  const range = firstWords(suite.model, 2).map((w) => w.toLowerCase());
  const rows = all || [];

  const sameBrand = (r) => String(r.brand || "").toLowerCase() === brand;
  const isUniversal = (r) => {
    const t = ((r.fits || "") + " " + (r.model || "")).toLowerCase();
    return UNIVERSAL.some((u) => t.includes(u));
  };
  const namesRange = (r) => {
    const t = ((r.fits || "") + " " + (r.model || "")).toLowerCase();
    return range.some((w) => w.length > 2 && t.includes(w));
  };

  // SEATS - only offer a seat that actually names this range, or a same-brand adjustable seat.
  const seats = rows
    .filter((r) => r.category === "toilet seat")
    .filter((r) => (sameBrand(r) && (namesRange(r) || isUniversal(r))) || namesRange(r))
    .sort((a, b) => (namesRange(b) ? 1 : 0) - (namesRange(a) ? 1 : 0));

  // INLET VALVES - driven by what the USER told us, never by the photo.
  const want = INLET_SYNONYMS[inlet] || [];
  const inletValves = rows
    .filter((r) => r.category === "toilet inlet valve")
    .filter((r) => {
      if (!want.length) return sameBrand(r) || isUniversal(r);
      const pos = String(r.size || "").toLowerCase();
      const matchesInlet = want.some((w) => pos.includes(w));
      return matchesInlet && (sameBrand(r) || isUniversal(r) || namesRange(r));
    })
    .sort((a, b) => (sameBrand(b) ? 1 : 0) - (sameBrand(a) ? 1 : 0));

  const outletValves = rows
    .filter((r) => r.category === "toilet outlet valve")
    .filter((r) => sameBrand(r) || isUniversal(r) || namesRange(r))
    .sort((a, b) => (sameBrand(b) ? 1 : 0) - (sameBrand(a) ? 1 : 0));

  const buttons = rows
    .filter((r) => r.category === "flush button")
    .filter((r) => sameBrand(r) || isUniversal(r) || namesRange(r))
    .sort((a, b) => (sameBrand(b) ? 1 : 0) - (sameBrand(a) ? 1 : 0));

  // Caroma fill valves are made by Geberit and carry GEBERIT branding on the body - warn the
  // plumber so they don't think they've been sent the wrong part.
  const geberitNote = inletValves.some((r) => String(r.fits || "").indexOf("Geberit-branded") !== -1);

  return Response.json({
    suite: card(suite),
    inlet: inlet || null,
    seats: seats.slice(0, 6).map(card),
    inletValves: inletValves.slice(0, 6).map(card),
    outletValves: outletValves.slice(0, 6).map(card),
    buttons: buttons.slice(0, 6).map(card),
    geberitNote,
  });
}
