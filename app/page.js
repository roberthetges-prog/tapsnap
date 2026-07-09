import Link from "next/link";
import parts from "../lib/parts.json";

export default function Home() {
  const brands = [...new Set(parts.map((p) => p.brand))];
  const total = parts.length;
  return (
    <main>
      <section className="hero">
        <div className="container">
          <span className="pill">Built for New Zealand plumbers</span>
          <h1>Find the right tap spare part in seconds.</h1>
          <p>
            Stop guessing at the merchant counter. Tell SpareMatch what you&apos;re looking at,
            answer a question or two, and get the exact cartridge, spindle, washer or aerator —
            with the part number and where to buy it.
          </p>
          <div className="actions">
            <Link href="/find" className="btn btn-primary">Find a part →</Link>
            <a href="#how" className="btn btn-ghost">How it works</a>
          </div>
        </div>
      </section>

      <section className="section" id="how">
        <div className="container">
          <h2>How it works</h2>
          <p className="lead">No account, no manuals — just a couple of taps.</p>
          <div className="steps">
            <div className="step">
              <div className="n">1</div>
              <h3>Snap or pick your brand</h3>
              <p>Take a photo of the tap or the removed cartridge, or just pick the brand you&apos;re working on.</p>
            </div>
            <div className="step">
              <div className="n">2</div>
              <h3>Answer a quick question</h3>
              <p>When the choice isn&apos;t obvious, SpareMatch asks one thing at a time — valve type, then size — to narrow it down.</p>
            </div>
            <div className="step">
              <div className="n">3</div>
              <h3>Get the exact part</h3>
              <p>See the part number, a reference photo, any supersession, and a link to buy it. Fewer trips back to the van.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section" style={{ background: "#fff", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
        <div className="container">
          <h2>{brands.length} brands, {total}+ genuine parts and growing</h2>
          <p className="lead">Every part number is sourced from a manufacturer or retailer listing — nothing made up.</p>
          <div className="brands">
            {brands.map((b) => (
              <span className="brand-chip" key={b}>{b}</span>
            ))}
          </div>
          <p className="note">
            Starting with tapware spares. Hot water / califonts, cylinders and fittings are on the roadmap.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container" style={{ textAlign: "center" }}>
          <h2>Ready to find a part?</h2>
          <p className="lead" style={{ marginBottom: 20 }}>It takes about ten seconds.</p>
          <Link href="/find" className="btn btn-primary">Find a part →</Link>
        </div>
      </section>
    </main>
  );
}
