"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, getToken } from "@/lib/api";

export default function Judge() {
  const router = useRouter();
  const [locked, setLocked] = useState(false);
  const [list, setList] = useState<any[] | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try { setList(await api.tournaments()); }
    catch (e: any) { if (e.message.includes("Pro feature")) setLocked(true); }
  }
  useEffect(() => {
    if (!getToken()) { router.replace("/login?next=/judge"); return; }
    load();
  }, [router]);

  async function create() {
    if (!name.trim()) return;
    setBusy(true);
    try { const t = await api.createTournament(name); router.push(`/judge/${t.id}`); }
    finally { setBusy(false); }
  }

  if (locked) return (
    <main className="max-w-xl mx-auto px-6 pt-20 text-center">
      <p className="eyebrow mb-2">Pro feature</p>
      <h1 className="font-display text-3xl font-bold mb-3">Tournament Judge Mode</h1>
      <p className="text-parchment/60 mb-6">Score every speaker in a debate or MUN, rank them on a live leaderboard, and export results. Available on Pro and Org.</p>
      <Link href="/pricing" className="px-6 py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90">See plans →</Link>
    </main>
  );

  return (
    <main className="max-w-3xl mx-auto px-6 pt-12 pb-20">
      <p className="eyebrow mb-2">Judge Mode</p>
      <h1 className="font-display text-3xl font-bold mb-6">Tournaments</h1>

      <div className="flex gap-2 mb-8">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="New tournament name (e.g. LUMS MUN 2026)"
          onKeyDown={(e) => e.key === "Enter" && create()}
          className="flex-1 bg-panel border border-line rounded-md px-4 py-2.5 outline-none focus:border-amber" />
        <button onClick={create} disabled={busy} className="px-5 rounded-md bg-amber text-ink font-medium hover:bg-amber/90 disabled:opacity-50">
          {busy ? "…" : "Create"}
        </button>
      </div>

      {!list ? <p className="text-unverified">Loading…</p> : list.length === 0 ? (
        <p className="text-parchment/50">No tournaments yet. Create one to start scoring speakers.</p>
      ) : (
        <div className="space-y-2">
          {list.map((t) => (
            <Link key={t.id} href={`/judge/${t.id}`} className="flex justify-between items-center bg-panel border border-line rounded-lg px-5 py-4 hover:border-amber">
              <span className="font-display text-lg">{t.name}</span>
              <span className="font-mono text-xs text-unverified">{t.entries} speaker{t.entries === 1 ? "" : "s"}</span>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
