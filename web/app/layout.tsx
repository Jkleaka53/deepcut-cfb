import type { Metadata } from "next";
import Link from "next/link";
import Disclaimer from "@/components/Disclaimer";
import "./globals.css";

export const metadata: Metadata = {
  title: "CFB Matchups",
  description: "College football games broken down on statistics. Not for gambling or betting.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <nav className="nav">
          <div className="wrap">
            <Link href="/" className="brand">CFB Matchups</Link>
            <Link href="/#games" className="link">Games</Link>
            <Link href="/#my-teams" className="link">My Teams</Link>
          </div>
        </nav>
        <main>
          <div className="wrap">{children}</div>
        </main>
        <Disclaimer />
      </body>
    </html>
  );
}
