import Link from "next/link";

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section className="mb-10">
    <h2 className="font-display text-2xl text-amber mb-3">{title}</h2>
    <div className="text-parchment/70 text-sm leading-relaxed space-y-2">{children}</div>
  </section>
);

export default function Methodology() {
  return (
    <main className="max-w-2xl mx-auto px-6 pt-12 pb-24">
      <p className="eyebrow mb-2">Transparency</p>
      <h1 className="font-display text-4xl font-bold mb-3">How verdicts are reached</h1>
      <p className="text-parchment/60 mb-10">
        We publish our method because a fact-checker is only as trustworthy as its
        reasoning is auditable. Here is exactly how a claim becomes a verdict — and
        where the limits are.
      </p>

      <Section title="The pipeline">
        <p>Speech is transcribed (Whisper), check-worthy claims and named entities are
        extracted, each claim is searched on the open web, and retrieved evidence is
        compared to the claim with a natural-language-inference model trained on the
        FEVER fact-verification dataset. Quotes are matched semantically, not literally.</p>
      </Section>

      <Section title="Source credibility tiers">
        <p><span className="text-verified font-medium">High</span> — governments, UN bodies, the World Bank, peer-reviewed and academic sources.</p>
        <p><span className="text-misleading font-medium">Medium</span> — established news organizations and reference works.</p>
        <p><span className="text-unverified font-medium">Low</span> — everything else; shown for context but never used to decide a verdict.</p>
      </Section>

      <Section title="The rules that prevent one-sided verdicts">
        <p>• A claim is <span className="text-verified">Verified</span> or <span className="text-false">Likely False</span> only when <b>two or more independent credible sources</b> agree. Multiple pages from the same outlet count as one source.</p>
        <p>• When credible sources both support and contradict a claim, the verdict is <span className="text-misleading">Disputed</span> — both sides are shown and no winner is declared.</p>
        <p>• A single credible source yields only <span className="text-partial">Partially Supported / Disputed</span>, flagged as preliminary.</p>
        <p>• When no credible evidence is found, the verdict is <span className="text-unverified">Insufficient Evidence</span> — we never guess.</p>
        <p>• Supporting and contradicting evidence are always displayed together.</p>
      </Section>

      <Section title="The credibility score">
        <p>The 0–10 speaker score blends three sub-scores — factual accuracy, integrity
        (manipulation, fallacies, fake quotes) and delivery — using weights <b>you</b> set
        on the Scoring page. The weighting is yours, and it is shown, so the score is never
        a black box.</p>
      </Section>

      <Section title="Known limitations & bias">
        <p>No automated fact-checker is free of bias. Our results depend on what the web
        returns, on the credibility tiers we assign, and on a model whose training data
        carries its own slant. We reduce — not eliminate — bias by requiring corroboration,
        surfacing disagreement, refusing to guess, and showing every source. Treat verdicts
        as evidence-backed signals for human judgement, not final truth.</p>
      </Section>

      <Link href="/analyze" className="inline-block mt-4 px-6 py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90">Try an analysis →</Link>
    </main>
  );
}
