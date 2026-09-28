import Link from "next/link";

export default function Landing() {
  return (
    <main className="px-6 md:px-10">
      {/* Hero — signature verdict stamp */}
      <section className="max-w-5xl mx-auto pt-16 md:pt-24 pb-20">
        <p className="eyebrow mb-5">AI rhetorical intelligence · fact verification</p>
        <div className="grid md:grid-cols-[1.4fr_1fr] gap-10 items-center">
          <div>
            <h1 className="font-display text-4xl md:text-6xl leading-[1.05] font-bold">
              Every claim in a speech,
              <span className="text-amber"> put on the record.</span>
            </h1>
            <p className="mt-6 text-parchment/70 text-lg max-w-md">
              Paste a transcript or upload audio. DebateIQ detects the quotes, statistics
              and factual claims, checks them against live sources, and scores the speaker
              the way a debate judge would.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/analyze?mode=text" className="px-5 py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90">
                Analyze text →
              </Link>
              <Link href="/analyze?mode=audio" className="px-5 py-3 rounded-md border border-line text-parchment hover:border-amber">
                Upload audio
              </Link>
            </div>
          </div>

          {/* the stamped claim card */}
          <div className="relative bg-panel border border-line rounded-xl p-6">
            <p className="eyebrow mb-3">Claim under review</p>
            <p className="font-display text-lg leading-snug">
              “The World Bank reported that 70% of Pakistan’s youth are unemployed.”
            </p>
            <div className="mt-5 h-px bg-line" />
            <p className="mt-3 text-xs text-parchment/50 font-mono">
              Sources checked · evidence ranked · attribution tested
            </p>
            <div className="stamp absolute -top-3 -right-2 border-4 border-false text-false font-display font-bold
                            rounded-md px-3 py-1 text-sm tracking-wide bg-ink/80">
              POTENTIALLY FALSE
            </div>
          </div>
        </div>
      </section>

      {/* How it works — a real sequence, so numbered markers are earned */}
      <section className="max-w-5xl mx-auto pb-20">
        <p className="eyebrow mb-6">How it works</p>
        <ol className="grid md:grid-cols-4 gap-4">
          {[
            ["01", "Capture", "Paste text or upload audio. Whisper transcribes speech to text."],
            ["02", "Detect", "NLP isolates check-worthy claims, quotes and named entities."],
            ["03", "Verify", "Live web evidence is ranked and tested with a FEVER-trained model."],
            ["04", "Judge", "Verdicts, manipulation risk and a credibility score you can tune."],
          ].map(([n, t, d]) => (
            <li key={n} className="bg-panel border border-line rounded-xl p-5">
              <span className="font-mono text-amber text-sm">{n}</span>
              <h3 className="font-display text-xl mt-2">{t}</h3>
              <p className="text-parchment/60 text-sm mt-2">{d}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* What it catches */}
      <section className="max-w-5xl mx-auto pb-24">
        <div className="grid md:grid-cols-3 gap-4">
          {[
            ["Quote authenticity", "Did they really say it? Semantic matching, not literal wording."],
            ["Manipulation risk", "Vague sourcing, fear language and false certainty, flagged."],
            ["Pakistani context", "Roman-Urdu code-switching, MUN register and common fake stats."],
          ].map(([t, d]) => (
            <div key={t} className="border border-line rounded-xl p-5">
              <h3 className="font-display text-lg text-amber">{t}</h3>
              <p className="text-parchment/60 text-sm mt-2">{d}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 text-center">
          <Link href="/signup" className="px-6 py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90">
            Create a free account
          </Link>
          <p className="mt-3 text-xs text-unverified font-mono">
            Free tier · up to 300 words or 60 seconds per analysis
          </p>
        </div>
      </section>
    </main>
  );
}
