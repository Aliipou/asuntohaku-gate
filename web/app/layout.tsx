import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

// "latin-ext" is included alongside "latin" so ä/ö/å and other Finnish
// diacritics are covered by the subsetted, self-hosted font file rather than
// falling back to a system font mid-word.
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Asuntohaku",
  description: "Vuokra- ja myyntiasuntojen haku.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fi" className={`${geistSans.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-paper text-ink">{children}</body>
    </html>
  );
}
