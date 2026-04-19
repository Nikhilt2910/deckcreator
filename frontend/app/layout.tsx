import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "DeckCreator Studio",
  description: "Generate presentation-ready decks from business data and brand references.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="ambient ambient-a" />
        <div className="ambient ambient-b" />
        <div className="grid-overlay" />
        <div className="shell">
          <header className="topbar">
            <Link href="/" className="brand">
              <span className="brand-mark">DC</span>
              <span className="brand-copy">
                <strong>DeckCreator</strong>
                <span>Studio</span>
              </span>
            </Link>
            <nav className="nav">
              <Link href="/upload">Create</Link>
              <Link href="/status">Track</Link>
              <Link href="/tickets">Support</Link>
            </nav>
          </header>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
