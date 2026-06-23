"use client";

const VERDICT: Record<string, { text: string; border: string; label: string }> = {
  "Verified": { text: "text-verified", border: "border-verified", label: "VERIFIED" },
  "Partially Supported": { text: "text-partial", border: "border-partial", label: "PARTIALLY SUPPORTED" },
  "Disputed": { text: "text-misleading", border: "border-misleading", label: "DISPUTED" },
  "Partially Disputed": { text: "text-misleading", border: "border-misleading", label: "PARTIALLY DISPUTED" },
  "Likely False": { text: "text-false", border: "border-false", label: "LIKELY FALSE" },
  "Insufficient Evidence": { text: "text-unverified", border: "border-unverified", label: "INSUFFICIENT EVIDENCE" },
};
const TIER: Record<string, string> = { High: "bg-verified", Medium: "bg-misleading", Low: "bg-unverified" };
const RISK: Record<string, string> = { Low: "text-verified", Medium: "text-misleading", High: "text-false" };

function Bar({ pct, cls }: { pct: number; cls: string }) {
  return <div className="h-2 bg-line rounded-full overflow-hidden"><div className={`h-full ${cls}`} style={{ width: `${pct}%` }} /></div>;
}

function EvidenceItem({ e }: { e: any }) {
  return (
    <div className="bg-ink rounded p-2 mt-1.5">
      <a href={e.url} target="_blank" className="text-sm text-amber hover:underline">{e.title?.slice(0, 80)}</a>
      <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded text-ink ${TIER[e.tier]}`}>{e.tier}</span>
      <p className="text-xs text-unverified mt-1">{e.snippet?.slice(0, 130)}…</p>
    </div>
  );
}

export default function Dashboard({ data }: { data: any }) {
  const j = data.judge, sub = j.subscores, c = j.counts;
  const scoreColor = j.score >= 7 ? "text-verified" : j.score >= 4 ? "text-misleading" : "text-false";

  return (
    <div className="space-y-4">
      {data.translation?.translated && (
        <div className="border border-amber/40 bg-amber/10 rounded-lg px-4 py-3 text-sm text-amber">
          Analyzed via automatic translation from {data.translation.language_label}. Translation may introduce errors; verdicts are best-effort.
        </div>
      )}
      <div className="text-[11px] font-mono text-unverified">
        Verification engine: {data.engine === "llm" ? "AI reasoning" : "local models"}
      </div>
      {(data.meta?.truncated || data.meta?.trimmed) && (
        <div className="border border-misleading/40 bg-misleading/10 rounded-lg px-4 py-3 text-sm text-misleading">
          Free tier: {data.meta.truncated
            ? `analyzed the first ${data.meta.word_cap} of ${data.meta.original_words} words.`
            : `analyzed the first ${data.meta.audio_cap_sec}s of ${data.meta.original_seconds}s of audio.`}
        </div>
      )}

      {/* Score + judge */}
      <div className="bg-panel border border-line rounded-xl p-6">
        <div className="flex justify-between items-start gap-6">
          <div>
            <p className="eyebrow mb-1">Speaker credibility</p>
            <div className={`font-display font-bold text-5xl ${scoreColor}`}>{j.score}<span className="text-unverified text-2xl">/10</span></div>
            <p className="text-[11px] text-unverified font-mono mt-1">avg {j.avg_sources} independent sources / claim</p>
          </div>
          <div className="text-right text-sm text-parchment/70 font-mono leading-relaxed">
            <div className="text-verified">✓ {c.supported} supported</div>
            <div className="text-misleading">~ {c.disputed} disputed</div>
            <div className="text-false">✗ {c.false} likely false</div>
            <div className="text-unverified">? {c.insufficient} unverifiable</div>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-5">
          {[["Factual", sub.factual], ["Integrity", sub.integrity], ["Delivery", sub.delivery]].map(([k, v]: any) => (
            <div key={k}>
              <div className="flex justify-between text-xs text-parchment/60 mb-1 font-mono"><span>{k}</span><span>{v}/10</span></div>
              <Bar pct={v * 10} cls="bg-amber" />
            </div>
          ))}
        </div>
        <p className="mt-5 text-parchment/80 text-sm"><span className="text-amber font-medium">AI Judge — </span>{j.summary}</p>
      </div>

      {/* alerts */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-panel border border-line rounded-xl p-5">
          <p className="eyebrow mb-2">Manipulation risk</p>
          <p className={`font-display text-2xl ${RISK[data.manipulation.level]}`}>{data.manipulation.level}</p>
          <ul className="mt-2 text-xs text-parchment/60 space-y-1">{data.manipulation.reasons.map((r: string, i: number) => <li key={i}>• {r}</li>)}</ul>
        </div>
        <div className="bg-panel border border-line rounded-xl p-5">
          <p className="eyebrow mb-2">Logic</p>
          {data.fallacies.length ? data.fallacies.map((f: any, i: number) => (
            <div key={i} className="mb-2"><span className="text-misleading font-medium text-sm">{f.fallacy}</span><p className="text-xs text-parchment/60">{f.explanation}</p></div>
          )) : <p className="text-sm text-parchment/50">No fallacies detected.</p>}
        </div>
        <div className="bg-panel border border-line rounded-xl p-5">
          <p className="eyebrow mb-2">Pakistani context</p>
          <ul className="text-xs text-parchment/60 space-y-1">{data.pakistani.flags.map((f: string, i: number) => <li key={i}>• {f}</li>)}</ul>
        </div>
      </div>

      {/* metrics */}
      <div className="bg-panel border border-line rounded-xl p-5">
        <p className="eyebrow mb-3">Speech analytics</p>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {[["Words", data.metrics.words], ["WPM", data.metrics.wpm ?? "—"], ["Confidence", data.metrics.confidence_level],
            ["Fillers", data.metrics.filler_usage], ["Filler %", data.metrics.filler_pct + "%"], ["Arg. density", data.metrics.argument_density]
          ].map(([k, v]: any) => (
            <div key={k} className="text-center bg-ink rounded-lg py-3"><div className="font-mono text-amber text-lg">{v}</div><div className="text-[10px] text-unverified uppercase tracking-wide">{k}</div></div>
          ))}
        </div>
      </div>

      {/* quotes */}
      {data.quotes.length > 0 && (
        <div className="bg-panel border border-line rounded-xl p-5">
          <p className="eyebrow mb-3">Quote authenticity</p>
          {data.quotes.map((q: any, i: number) => (
            <div key={i} className="border-l-2 border-line pl-3 mb-3">
              <p className="font-display italic">“{q.quote}”</p>
              <p className="text-xs text-parchment/60">{q.attributed_to || "Unknown"} · <span className="text-amber">{q.status}</span> ({Math.round(q.confidence * 100)}%)</p>
              <p className="text-xs text-unverified">{q.notes}</p>
            </div>
          ))}
        </div>
      )}

      {/* claims — both sides always shown */}
      <div className="bg-panel border border-line rounded-xl p-5">
        <p className="eyebrow mb-3">Claim verification</p>
        {data.claims.length === 0 && <p className="text-sm text-parchment/50">No check-worthy claims detected.</p>}
        {data.claims.map((cl: any, i: number) => {
          const v = VERDICT[cl.label] || VERDICT["Insufficient Evidence"];
          const div = cl.diversity;
          return (
            <div key={i} className={`border border-line border-l-4 ${v.border} rounded-lg p-4 mt-3`}>
              <div className="flex justify-between items-center flex-wrap gap-2">
                <span className={`text-xs font-mono font-bold ${v.text}`}>{v.label}</span>
                <div className="flex items-center gap-2">
                  {div.single_source && <span className="text-[10px] text-misleading border border-misleading/40 rounded px-1.5 py-0.5">single source</span>}
                  <span className="text-[10px] text-unverified font-mono">{div.independent_sources} independent · conf {Math.round(cl.confidence * 100)}%</span>
                </div>
              </div>
              <Bar pct={Math.round(cl.confidence * 100)} cls="bg-amber mt-2" />
              <p className="my-2">“{cl.claim}”</p>
              <p className="text-sm text-parchment/70"><span className="text-amber">Why — </span>{cl.note}</p>
              <div className="grid md:grid-cols-2 gap-3 mt-3">
                <div>
                  <p className="text-[11px] font-mono text-verified mb-1">SUPPORTS ({cl.supporting.length})</p>
                  {cl.supporting.length ? cl.supporting.map((e: any, k: number) => <EvidenceItem key={k} e={e} />) : <p className="text-xs text-unverified">None found.</p>}
                </div>
                <div>
                  <p className="text-[11px] font-mono text-false mb-1">DISPUTES ({cl.contradicting.length})</p>
                  {cl.contradicting.length ? cl.contradicting.map((e: any, k: number) => <EvidenceItem key={k} e={e} />) : <p className="text-xs text-unverified">None found.</p>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
