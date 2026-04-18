import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "DeckCreator",
  description: "FastAPI + Next.js workflow for deck generation and ticketing.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <Link href="/" className="brand">
              DeckCreator
            </Link>
            <nav className="nav">
              <Link href="/upload">Upload</Link>
              <Link href="/tickets">Tickets</Link>
              <Link href="/status">Status</Link>
            </nav>
          </header>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
