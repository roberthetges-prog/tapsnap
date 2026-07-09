// Pure, framework-agnostic matching logic for SpareMatch NZ.
const norm = (v) => (v == null ? "" : String(v).trim());

function distinct(parts, field) {
  const m = new Map();
  for (const p of parts) {
    const v = norm(p[field]);
    if (!v) continue;
    m.set(v, (m.get(v) || 0) + 1);
  }
  return [...m.entries()]
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value, undefined, { numeric: true }));
}

export function listBrands(parts) {
  return distinct(parts, "brand").map((b) => ({ brand: b.value, count: b.count }));
}

export function applyFilters(parts, sel = {}) {
  return parts.filter((p) =>
    Object.entries(sel).every(([f, v]) => !v || norm(p[f]) === norm(v))
  );
}

// Size is the key question for single-lever cartridges, so it comes before valve type.
const QUESTIONS = [
  { field: "category", label: "What kind of part is it?" },
  { field: "dimension", label: "What size is the cartridge? (measure the diameter across the round body)" },
  { field: "valveType", label: "What type of valve / mechanism?" },
];

export function nextQuestion(parts, sel = {}) {
  const remaining = applyFilters(parts, sel);
  for (const q of QUESTIONS) {
    if (sel[q.field]) continue;
    const opts = distinct(remaining, q.field);
    if (opts.length > 1) {
      return { field: q.field, label: q.label, options: opts, remaining: remaining.length };
    }
  }
  return null;
}

export function evaluate(parts, sel = {}) {
  const matches = applyFilters(parts, sel);
  const question = nextQuestion(parts, sel);
  return { matches, question, count: matches.length };
}
