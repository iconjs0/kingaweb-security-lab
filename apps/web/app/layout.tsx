import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import { TopNav } from "@kingaweb/design-system";
import "./globals.css";

const ui = Space_Grotesk({ subsets: ["latin"], variable: "--font-ui", display: "swap" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "KingaWeb Security Lab",
  description: "Authorized web/API security training — guided labs, challenges, assessments.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" className={`${ui.variable} ${mono.variable}`}>
      <body>
        <TopNav />
        <main id="main" style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 20px 64px" }}>
          {children}
        </main>
        <footer style={{ borderTop: "1px solid var(--line-1)", padding: "16px 20px", color: "var(--text-3)", fontSize: "var(--fs-small)" }}>
          <div style={{ maxWidth: 1200, margin: "0 auto" }}>
            Authorized learning environment only. Test your assigned session targets — never external systems.
          </div>
        </footer>
      </body>
    </html>
  );
}
