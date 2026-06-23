"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, setSession } from "@/lib/api";

export default function Signup() {
  const router = useRouter();
  const [u, setU] = useState(""); const [p, setP] = useState("");
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);

  async function submit() {
    setErr(""); setBusy(true);
    try {
      const r = await api.signup(u, p);
      setSession(r.token, r.username);
      router.push("/analyze");
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }

  return (
    <main className="max-w-sm mx-auto px-6 pt-20">
      <p className="eyebrow mb-2">Free tier</p>
      <h1 className="font-display text-3xl font-bold mb-6">Create account</h1>
      <div className="space-y-3">
        <input className="w-full bg-panel border border-line rounded-md px-4 py-3 outline-none focus:border-amber"
               placeholder="Username (3+ chars)" value={u} onChange={e => setU(e.target.value)} />
        <input type="password" className="w-full bg-panel border border-line rounded-md px-4 py-3 outline-none focus:border-amber"
               placeholder="Password (6+ chars)" value={p} onChange={e => setP(e.target.value)}
               onKeyDown={e => e.key === "Enter" && submit()} />
        {err && <p className="text-false text-sm">{err}</p>}
        <button onClick={submit} disabled={busy}
                className="w-full py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90 disabled:opacity-50">
          {busy ? "Creating…" : "Create account"}
        </button>
      </div>
      <p className="mt-5 text-sm text-parchment/60">
        Already have one? <Link href="/login" className="text-amber">Log in</Link>
      </p>
    </main>
  );
}
