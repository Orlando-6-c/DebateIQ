"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, setSession } from "@/lib/api";

function LoginForm() {
  const router = useRouter();
  const next = useSearchParams().get("next") || "/analyze";
  const [u, setU] = useState(""); const [p, setP] = useState("");
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);

  async function submit() {
    setErr(""); setBusy(true);
    try {
      const r = await api.login(u, p);
      setSession(r.token, r.username);
      router.push(next);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }

  return (
    <main className="max-w-sm mx-auto px-6 pt-20">
      <p className="eyebrow mb-2">Welcome back</p>
      <h1 className="font-display text-3xl font-bold mb-6">Log in</h1>
      <div className="space-y-3">
        <input className="w-full bg-panel border border-line rounded-md px-4 py-3 outline-none focus:border-amber"
               placeholder="Username" value={u} onChange={e => setU(e.target.value)} />
        <input type="password" className="w-full bg-panel border border-line rounded-md px-4 py-3 outline-none focus:border-amber"
               placeholder="Password" value={p} onChange={e => setP(e.target.value)}
               onKeyDown={e => e.key === "Enter" && submit()} />
        {err && <p className="text-false text-sm">{err}</p>}
        <button onClick={submit} disabled={busy}
                className="w-full py-3 rounded-md bg-amber text-ink font-medium hover:bg-amber/90 disabled:opacity-50">
          {busy ? "Checking…" : "Log in"}
        </button>
      </div>
      <p className="mt-5 text-sm text-parchment/60">
        No account? <Link href="/signup" className="text-amber">Sign up</Link>
      </p>
    </main>
  );
}

export default function Login() {
  return <Suspense><LoginForm /></Suspense>;
}
