"use client";
import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, getToken } from "@/lib/api";
import Dashboard from "@/components/Dashboard";

function Analyze() {
  const router = useRouter();
  const params = useSearchParams();
  const [mode, setMode] = useState<"text" | "audio">((params.get("mode") as any) || "text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState<any>(null);
  const [lim, setLim] = useState<{ word: number; audio: number; monthly: number | null; tier: string }>({ word: 300, audio: 60, monthly: 25, tier: "Free" });
  const [used, setUsed] = useState(0);

  useEffect(() => {
    if (!getToken()) { router.replace(`/login?next=/analyze?mode=${mode}`); return; }
    api.me().then((m) => {
      setLim({ word: m.limits.word_cap, audio: m.limits.audio_sec, monthly: m.limits.monthly_analyses, tier: m.tier_label });
      setUsed(m.usage.used || 0);
    }).catch(() => {});
  }, [mode, router]);

  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const over = words > lim.word;
  const limitErr = err && (err.includes("limit") || err.includes("Pro"));

  async function run() {
    setErr(""); setResult(null); setBusy(true);
    try {
      const data = mode === "text" ? await api.analyzeText(text) : await api.analyzeAudio(file!);
      setResult(data);
      if (data.meta?.usage) setUsed(data.meta.usage.used);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }

  return (
    <main className="max-w-3xl mx-auto px-6 pt-10 pb-20">
      <div className="flex justify-between items-center mb-6">
        <div>
          <p className="eyebrow mb-2">New analysis</p>
          <h1 className="font-display text-3xl font-bold">Put a speech on the record</h1>
        </div>
        <div className="text-right text-xs font-mono text-unverified">
          <div className="text-amber uppercase">{lim.tier} plan</div>
          {lim.monthly ? <div>{used}/{lim.monthly} used this month</div> : <div>unlimited</div>}
        </div>
      </div>

      <div className="inline-flex rounded-md border border-line overflow-hidden mb-5">
        {(["text", "audio"] as const).map((m) => (
          <button key={m} onClick={() => { setMode(m); setResult(null); }}
            className={`px-5 py-2 text-sm capitalize ${mode === m ? "bg-amber text-ink" : "text-parchment/70"}`}>
            {m === "text" ? "Paste text" : "Upload audio"}
          </button>
        ))}
      </div>

      {mode === "text" ? (
        <div>
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={8} placeholder="Paste a transcript or speech…"
            className="w-full bg-panel border border-line rounded-md p-4 outline-none focus:border-amber" />
          <div className={`text-xs font-mono mt-1 ${over ? "text-misleading" : "text-unverified"}`}>
            {words}/{lim.word} words {over && `· only the first ${lim.word} will be analyzed`}
          </div>
        </div>
      ) : (
        <div className="border border-dashed border-line rounded-md p-6 text-center">
          <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] || null)} className="text-sm text-parchment/70" />
          <p className="text-xs text-unverified font-mono mt-2">Analyzes the first {lim.audio} seconds on your plan.</p>
          {file && <p className="text-sm text-amber mt-2">{file.name}</p>}
        </div>
      )}

      {err && (
        <div className="text-sm mt-3">
          <p className="text-false">{err}</p>
          {limitErr && <Link href="/pricing" className="text-amber underline">Upgrade to Pro →</Link>}
        </div>
      )}

      <button onClick={run} disabled={busy || (mode === "text" ? !text.trim() : !file)}
        className="mt-5 px-6 py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90 disabled:opacity-40">
        {busy ? "Analyzing… (first run loads models, ~1–2 min)" : "Analyze"}
      </button>

      {result && <div className="mt-8"><Dashboard data={result} /></div>}
    </main>
  );
}

export default function Page() {
  return <Suspense><Analyze /></Suspense>;
}
