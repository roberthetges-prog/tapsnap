export const metadata = {
  title: "Privacy Policy — TapSnap",
  description: "How TapSnap handles photos and data.",
};

export default function Privacy() {
  return (
    <main className="container prose" style={{ maxWidth: 760, padding: "32px 20px 64px" }}>
      <h1>Privacy Policy</h1>
      <p style={{ color: "#5b6875" }}>Last updated: 10 July 2026</p>

      <p>
        TapSnap helps you identify the correct spare part for a tap, mixer, valve or cartridge. This policy
        explains what we do — and don&apos;t do — with your information.
      </p>

      <h2>No account, no sign-up</h2>
      <p>
        You can use TapSnap without creating an account or giving us your name, email or phone number. We do
        not ask you to register.
      </p>

      <h2>Photos you upload</h2>
      <p>
        When you take or upload a photo of a part, the image is sent to our matching service and to the
        third-party AI providers that power identification (Jina AI for visual matching and Anthropic for
        image analysis). The photo is used only to identify the part you&apos;re looking at. We do not use your
        photos to identify you, we do not sell them, and we do not add them to a public gallery. Photos are
        processed to return a result and are not kept in a user profile.
      </p>

      <h2>Camera</h2>
      <p>
        The app can access your camera only when you choose to take a photo. Nothing is captured in the
        background, and you can decline the camera permission and upload an existing photo instead.
      </p>

      <h2>What we don&apos;t collect</h2>
      <p>
        We don&apos;t use advertising or third-party tracking cookies, and we don&apos;t build an advertising
        profile of you. Like most websites, our hosting provider (Vercel) may record basic, non-identifying
        request logs for security and reliability.
      </p>

      <h2>Links to retailers</h2>
      <p>
        Results may include links to manufacturer or retailer websites so you can buy the part. Those sites
        have their own privacy policies, which we don&apos;t control.
      </p>

      <h2>Children</h2>
      <p>TapSnap is a tool for tradespeople and homeowners and is not directed at children.</p>

      <h2>Changes</h2>
      <p>
        If this policy changes, we&apos;ll update the date at the top of this page.
      </p>

      <h2>Contact</h2>
      <p>
        Questions about privacy? Email <a href="mailto:myhappyplace@web.de">myhappyplace@web.de</a>.
      </p>
    </main>
  );
}
