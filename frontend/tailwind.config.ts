import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A0F1F", panel: "#111829", line: "#1E293B",
        amber: "#E8B04B", parchment: "#EDE8DC",
        verified: "#3FB950", partial: "#9BBF3A",
        misleading: "#E8A13B", false: "#F0533F", unverified: "#7A8699",
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        sans: ["var(--font-sans)", "system-ui"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
