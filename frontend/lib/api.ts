"use client";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860";

export function getToken() { return typeof window === "undefined" ? null : localStorage.getItem("diq_token"); }
export function getUsername() { return typeof window === "undefined" ? null : localStorage.getItem("diq_user"); }
export function setSession(t: string, u: string) { localStorage.setItem("diq_token", t); localStorage.setItem("diq_user", u); }
export function clearSession() { localStorage.removeItem("diq_token"); localStorage.removeItem("diq_user"); }

async function req(path: string, opts: RequestInit = {}, auth = false) {
  const headers: Record<string, string> = { ...(opts.headers as any) };
  if (!(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (auth) { const t = getToken(); if (t) headers["Authorization"] = `Bearer ${t}`; }
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const api = {
  signup: (u: string, p: string) => req("/auth/signup", { method: "POST", body: JSON.stringify({ username: u, password: p }) }),
  login: (u: string, p: string) => req("/auth/login", { method: "POST", body: JSON.stringify({ username: u, password: p }) }),
  me: () => req("/me", {}, true),
  tiers: () => req("/tiers"),
  upgrade: (tier: string) => req("/billing/upgrade", { method: "POST", body: JSON.stringify({ tier }) }, true),
  saveSettings: (s: any) => req("/settings", { method: "PUT", body: JSON.stringify(s) }, true),
  analyzeText: (text: string, threshold = 0.4) => req("/analyze/text", { method: "POST", body: JSON.stringify({ text, threshold }) }, true),
  analyzeAudio: (file: File, threshold = 0.4) => {
    const fd = new FormData(); fd.append("file", file);
    return req(`/analyze/audio?threshold=${threshold}`, { method: "POST", body: fd }, true);
  },
  // Judge Mode
  tournaments: () => req("/tournaments", {}, true),
  createTournament: (name: string) => req("/tournaments", { method: "POST", body: JSON.stringify({ name }) }, true),
  getTournament: (id: number | string) => req(`/tournaments/${id}`, {}, true),
  addEntry: (id: number | string, speaker: string, text: string) =>
    req(`/tournaments/${id}/entries`, { method: "POST", body: JSON.stringify({ speaker, text }) }, true),
  transcribeEntry: (id: number | string, file: File) => {
    const fd = new FormData(); fd.append("file", file);
    return req(`/tournaments/${id}/transcribe`, { method: "POST", body: fd }, true);
  },
  async exportTournament(id: number | string, name: string) {
    const res = await fetch(`${API}/tournaments/${id}/export`, { headers: { Authorization: `Bearer ${getToken()}` } });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `${name}_results.csv`; a.click();
    URL.revokeObjectURL(url);
  },
};
