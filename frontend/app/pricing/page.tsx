"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getToken } from "@/lib/api";

export default function Pricing() {
  const router = useRouter();
  const [tiers, setTiers] = useState<any>(null);
  const [current, setCurrent] = useState<string>("");
  const [busy, setBusy] = useState("");

  useEffect(() => {
    api.tiers().then(setTiers).catch(() => {});
    if (getToken()) api.me().then((m) => setCurrent(m.tier)).catch(() => {});
  }, []);

  async function choose(key: string) {
    if (!getToken()) { router.push("/login?next=/pricing"); return; }
    setBusy(key);
    try { const m = await api.upgrade(key); setCurrent(m.tier); } finally { setBusy(""); }
  }

  const order = ["free", "pro", "org"];

  return (
    <main className="max-w-5xl mx-auto px-6 pt-12 pb-24">
      <p className="eyebrow mb-2">Plans</p>
      <h1 className="font-display text-4xl font-bold mb-2">Pricing</h1>
      <p className="text-parchment/60 mb-10">Start free. Upgrade when you need longer speeches, unlimited analyses, or Tournament Judge Mode.</p>

      {!tiers ? <p className="text-unverified">Loading…</p> : (
        <div className="grid md:grid-cols-3 gap-5">
          {order.map((key) => {
            const t = tiers[key];
            const isCurrent = current === key;
            const featured = key === "pro";
            return (
              <div key={key} className={`rounded-xl p-6 border ${featured ? "border-amber bg-panel" : "border-line bg-panel/60"}`}>
                {featured && <p className="eyebrow mb-2">Most popular</p>}
                <h3 className="font-display text-2xl">{t.label}</h3>
                <p className="font-mono text-amber text-lg mt-1">{t.price}</p>
                <p className="text-parchment/60 text-sm mt-2 min-h-[40px]">{t.blurb}</p>
                <ul className="mt-4 space-y-2 text-sm text-parchment/80">
                  <li>• {t.word_cap.toLocaleString()} words / analysis</li>
                  <li>• {t.audio_sec}s audio / analysis</li>
                  <li>• {t.monthly_analyses ? `${t.monthly_analyses} analyses / month` : "Unlimited analyses"}</li>
                  <li className={t.judge_mode ? "text-verified" : "text-unverified"}>{t.judge_mode ? "✓" : "✗"} Tournament Judge Mode</li>
                  <li className={t.history ? "text-verified" : "text-unverified"}>{t.history ? "✓" : "✗"} Saved history</li>
                </ul>
                <button disabled={isCurrent || busy === key} onClick={() => choose(key)}
                  className={`w-full mt-6 py-2.5 rounded-md font-medium disabled:opacity-50 ${featured ? "bg-amber text-ink hover:bg-amber/90" : "border border-line text-parchment hover:border-amber"}`}>
                  {isCurrent ? "Current plan" : busy === key ? "Switching…" : key === "free" ? "Downgrade" : "Choose " + t.label}
                </button>
              </div>
            );
          })}
        </div>
      )}
      <p className="mt-8 text-xs text-unverified font-mono">
        Demo billing — upgrades switch instantly. Real card payments (Stripe) plug in before launch.
      </p>
    </main>
  );
}
