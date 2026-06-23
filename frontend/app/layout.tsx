import type { Metadata } from "next";
import { Fraunces, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Nav from "@/components/Nav";

const display = Fraunces({ subsets: ["latin"], weight: ["400", "600", "700"], variable: "--font-display" });
const sans = Inter({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "DebateIQ Pakistan — AI Fact Verification",
  description: "Verify quotes, statistics and claims in any speech, in real time.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable} ${mono.variable}`}>
      <body className="font-sans min-h-screen">
        <Nav />
        {children}
        <footer className="border-t border-line mt-24 py-8 text-center text-unverified text-xs font-mono">
          <a href="/methodology" className="hover:text-amber">Methodology</a> · DebateIQ Pakistan · Built for fact-based debate · Free tier
        </footer>
      </body>
    </html>
  );
}
