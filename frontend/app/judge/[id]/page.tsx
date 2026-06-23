"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { api, getToken } from "@/lib/api";

const medal = (i: number) => (i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}`);

export default function TournamentDetail() {
  const router = useRouter();
  const id = useParams().id as string;
  const [t, setT] = useState<any>(null);
  const [mode, setMode] = useState<"text" | "audio">("text");
  const [speaker, setSpeaker] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [err, setErr] = useState("");
  const [hint, setHint] = useState("");

  async function load() {
    try { setT(await api.getTournament(id)); }
    catch (e: any) { if (e.message.includes("Pro")) router.replace("/pricing"); else setErr(e.message); }
  }
  useEffect(() => {
    if (!getToken()) { router.replace(`/login?next=/judge/${id}`); return; }
    load();
  }, [id]);

  async function transcribe() {
    if (!file) return;
    setTranscribing(true); setErr(""); setHint("");
    try {
      const r = await api.transcribeEntry(id, file);
      setText(r.transcript || "");
      if (r.suggested_name) { setSpeaker(r.suggested_name); setHint(`Detected name: ${r.suggested_name} — edit if wrong.`); }
      else setHint("No name detected — leave blank to auto-number, or type one.");
    } catch (e: any) { setErr(e.message); } finally { setTranscribing(false); }
  }

  async function addSpeaker() {
    if (!text.trim()) { setErr("Add or transcribe a speech first."); return; }
    setBusy(true); setErr("");
    try {
      const r = await api.addEntry(id, speaker, text); // blank speaker -> backend auto-detects or numbers
      setSpeaker(""); setText(""); setFile(null); setHint(`Added as "${r.speaker}".`);
      await load();
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }

  if (!t) return <main className="max-w-3xl mx-auto px-6 pt-20 text-unverified">{err || "Loading…"}</main>;
  const scoreColor = (s: number) => (s >= 7 ? "text-verified" : s >= 4 ? "text-misleading" : "text-false");

  return (
    <main className="max-w-3xl mx-auto px-6 pt-12 pb-20">
      <div className="flex justify-between items-center mb-6">
        <div><p className="eyebrow mb-1">Tournament</p><h1 className="font-display text-3xl font-bold">{t.name}</h1></div>
        {t.entries.length > 0 && (
          <button onClick={() => api.exportTournament(id, t.name)} className="text-sm border border-line rounded-md px-4 py-2 hover:border-amber">Export CSV</button>
        )}
      </div>

      <div className="bg-panel border border-line rounded-xl p-5 mb-8">
        <p className="eyebrow mb-3">Score a speaker</p>

        <div className="inline-flex rounded-md border border-line overflow-hidden mb-4">
          {(["text", "audio"] as const).map((m) => (
            <button key={m} onClick={() => { setMode(m); setErr(""); setHint(""); }}
              className={`px-4 py-1.5 text-sm capitalize ${mode === m ? "bg-amber text-ink" : "text-parchment/70"}`}>
              {m === "text" ? "Paste text" : "Upload audio"}
            </button>
          ))}
        </div>

        {mode === "audio" && (
          <div className="border border-dashed border-line rounded-md p-4 mb-3 text-center">
            <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] || null)} className="text-sm text-parchment/70" />
            {file && <button onClick={transcribe} disabled={transcribing}
              className="ml-3 px-4 py-1.5 rounded-md border border-amber text-amber text-sm hover:bg-amber/10 disabled:opacity-50">
              {transcribing ? "Transcribing…" : "Transcribe"}
            </button>}
          </div>
        )}

        <input value={speaker} onChange={(e) => setSpeaker(e.target.value)}
          placeholder="Speaker name — auto-detected, or leave blank for Speaker 1, 2, 3…"
          className="w-full bg-ink border border-line rounded-md px-4 py-2.5 mb-2 outline-none focus:border-amber" />
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5}
          placeholder={mode === "audio" ? "Transcript will appear here — you can edit it." : "Paste this speaker's speech…"}
          className="w-full bg-ink border border-line rounded-md px-4 py-2.5 outline-none focus:border-amber" />

        {hint && <p className="text-amber text-xs mt-2">{hint}</p>}
        {err && <p className="text-false text-sm mt-2">{err}</p>}
        <button onClick={addSpeaker} disabled={busy}
          className="mt-3 px-5 py-2.5 rounded-md bg-amber text-ink font-medium hover:bg-amber/90 disabled:opacity-50">
          {busy ? "Scoring…" : "Analyze & add to leaderboard"}
        </button>
      </div>

      <p className="eyebrow mb-3">Leaderboard</p>
      {t.entries.length === 0 ? <p className="text-parchment/50">No speakers scored yet.</p> : (
        <div className="space-y-2">
          {t.entries.map((e: any, i: number) => (
            <details key={i} className="bg-panel border border-line rounded-lg px-5 py-4 group">
              <summary className="flex justify-between items-center cursor-pointer list-none">
                <span className="flex items-center gap-3">
                  <span className="font-mono text-lg w-7 text-center">{medal(i)}</span>
                  <span className="font-display text-lg">{e.speaker}</span>
                </span>
                <span className="flex items-center gap-3">
                  <span className={`font-display font-bold text-2xl ${scoreColor(e.score)}`}>{e.score}<span className="text-unverified text-sm">/10</span></span>
                  <span className="text-unverified text-xs group-open:rotate-180 transition-transform">▾</span>
                </span>
              </summary>
              <div className="flex gap-4 mt-2 text-[11px] font-mono text-unverified pl-10">
                <span className="text-verified">{e.counts?.supported ?? 0} supported</span>
                <span className="text-misleading">{e.counts?.disputed ?? 0} disputed</span>
                <span className="text-false">{e.counts?.false ?? 0} false</span>
                <span>avg {e.avg_sources} sources</span>
              </div>
              <div className="mt-4 pl-10 space-y-3">
                {e.subscores && (
                  <div className="grid grid-cols-3 gap-3">
                    {[["Factual", e.subscores.factual], ["Integrity", e.subscores.integrity], ["Delivery", e.subscores.delivery]].map(([k, v]: any) => (
                      <div key={k}>
                        <div className="flex justify-between text-[11px] font-mono text-parchment/60 mb-1"><span>{k}</span><span>{v}/10</span></div>
                        <div className="h-1.5 bg-line rounded-full overflow-hidden"><div className="h-full bg-amber" style={{ width: `${(v / 10) * 100}%` }} /></div>
                      </div>
                    ))}
                  </div>
                )}
                {e.summary && <p className="text-sm text-parchment/70"><span className="text-amber">AI Judge — </span>{e.summary}</p>}
              </div>
            </details>
          ))}
        </div>
      )}
    </main>
  );
}
