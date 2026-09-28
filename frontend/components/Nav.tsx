"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getUsername, getToken, clearSession, api } from "@/lib/api";

export default function Nav() {
  const [user, setUser] = useState<string | null>(null);
  const [tier, setTier] = useState<string>("");
  const [judge, setJudge] = useState(false);

  useEffect(() => {
    setUser(getUsername());
    if (getToken()) api.me().then((m) => { setTier(m.tier_label); setJudge(m.limits.judge_mode); }).catch(() => {});
  }, []);

  return (
    <nav className="flex items-center justify-between px-6 md:px-10 py-4 border-b border-line">
      <Link href="/" className="flex items-center gap-2">
        <span className="text-amber font-display text-xl font-bold">Debate<span className="text-parchment">IQ</span></span>
        <span className="eyebrow hidden sm:inline">Pakistan</span>
      </Link>
      <div className="flex items-center gap-5 text-sm">
        <Link href="/analyze" className="text-parchment/80 hover:text-amber">Analyze</Link>
        <Link href="/pricing" className="text-parchment/80 hover:text-amber">Pricing</Link>
        {user ? (
          <>
            {judge && <Link href="/judge" className="text-parchment/80 hover:text-amber">Judge Mode</Link>}
            <Link href="/settings" className="text-parchment/80 hover:text-amber">Scoring</Link>
            {tier && <span className="font-mono text-[10px] uppercase tracking-wide border border-amber/40 text-amber rounded px-1.5 py-0.5">{tier}</span>}
            <span className="font-mono text-xs text-unverified hidden sm:inline">@{user}</span>
            <button onClick={() => { clearSession(); location.href = "/"; }} className="text-unverified hover:text-false">Sign out</button>
          </>
        ) : (
          <>
            <Link href="/login" className="text-parchment/80 hover:text-amber">Log in</Link>
            <Link href="/signup" className="px-3 py-1.5 rounded-md bg-amber text-ink font-medium hover:bg-amber/90">Sign up</Link>
          </>
        )}
      </div>
    </nav>
  );
}
