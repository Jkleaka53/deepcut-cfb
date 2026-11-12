import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, Inter } from "next/font/google";
import Disclaimer from "@/components/Disclaimer";
import TopBar from "@/components/TopBar";
import { THEME_BOOT } from "@/lib/theme";
import "./globals.css";

const display = Barlow_Condensed({
  weight: ["600", "700", "800", "900"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-display",
});
const body = Inter({ subsets: ["latin"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "DeepCut CFB",
  description: "College football games broken down on statistics. Not for gambling or betting.",
  appleWebApp: { title: "DeepCut" },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
      </head>
      <body>
        <TopBar />
        <main>
          <div className="wrap">{children}</div>
        </main>
        <Disclaimer />
      </body>
    </html>
  );
}
