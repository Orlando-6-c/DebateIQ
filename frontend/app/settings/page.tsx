"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getToken } from "@/lib/api";

export default function Settings() {
  const router = useRouter();
  const [s, setS] = useState({ w_factual: 60, w_integrity: 25, w_delivery: 15, manip_sensitivity: 1.0 });
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) { router.replace("/login?next=/settings"); return; }
    api.me().then(r => setS({ ...s, ...r.settings })).catch(() => {});
  }, [router]);

  const total = s.w_factual + s.w_integrity + s.w_delivery;

  function set(k: string, v: number) { setS({ ...s, [k]: v }); setSaved(false); }

  async function save() {
    setBusy(true);
    try { await api.saveSettings(s); setSaved(true); } finally { setBusy(false); }
  }

  const sliders = [
    ["w_factual", "Factual accuracy", "How much verified vs false claims weigh."],
    ["w_integrity", "Integrity", "Manipulation, fallacies and fake quotes."],
    ["w_delivery", "Delivery", "Confidence, fillers and argument density."],
  ] as const;

  return (
    <main className="max-w-2xl mx-auto px-6 pt-10 pb-20">
      <p className="eyebrow mb-2">Customize</p>
      <h1 className="font-display text-3xl font-bold mb-2">Scoring model</h1>
      <p className="text-parchment/60 text-sm mb-8">
        Decide how the credibility score is calculated. Weights are normalized, so they
        don’t need to sum to 100 — but the balance between them is what matters.
      </p>

      <div className="space-y-6">
        {sliders.map(([k, label, desc]) => (
          <div key={k} className="bg-panel border border-line rounded-xl p-5">
            <div className="flex justify-between mb-1">
              <span className="font-display text-lg">{label}</span>
              <span className="font-mono text-amber">{(s as any)[k]}</span>
            </div>
            <p className="text-xs text-parchment/50 mb-3">{desc}</p>
            <input type="range" min={0} max={100} value={(s as any)[k]}
              onChange={e => set(k, +e.target.value)} className="w-full" />
            <div className="text-[11px] text-unverified font-mono mt-1">
              ≈ {Math.round(((s as any)[k] / total) * 100)}% of final score
            </div>
          </div>
        ))}

        <div className="bg-panel border border-line rounded-xl p-5">
          <div className="flex justify-between mb-1">
            <span className="font-display text-lg">Manipulation sensitivity</span>
            <span className="font-mono text-amber">{s.manip_sensitivity.toFixed(1)}×</span>
          </div>
          <p className="text-xs text-parchment/50 mb-3">How harshly manipulation tactics cut the score.</p>
          <input type="range" min={0.5} max={2} step={0.1} value={s.manip_sensitivity}
            onChange={e => set("manip_sensitivity", +e.target.value)} className="w-full" />
        </div>
      </div>

      <button onClick={save} disabled={busy}
        className="mt-6 px-6 py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90 disabled:opacity-50">
        {busy ? "Saving…" : saved ? "Saved ✓" : "Save scoring model"}
      </button>
    </main>
  );
}
