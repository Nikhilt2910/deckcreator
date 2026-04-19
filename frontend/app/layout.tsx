import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { PixelField } from "@/components/pixel-field";

export const metadata: Metadata = {
  title: "DeckCreator Agent",
  description: "Prompt-first deck creation with live research, file attachments, and editable PPTX generation.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PixelField />
        <div className="ambient ambient-a" />
        <div className="ambient ambient-b" />
        <div className="grid-overlay" />
        <div className="shell">
          <header className="topbar">
            <Link href="/" className="brand">
              <span className="brand-mark">AI</span>
              <span className="brand-copy">
                <strong>DeckCreator</strong>
                <span>Agent</span>
              </span>
            </Link>
            <nav className="nav">
              <Link href="/">Agent</Link>
              <Link href="/tickets">Support</Link>
            </nav>
          </header>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
