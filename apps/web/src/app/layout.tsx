import type { Metadata } from "next";
import localFont from "next/font/local";

import "katex/dist/katex.min.css";
import "./globals.css";

const figtree = localFont({
  src: "../beta-kit/fonts/Figtree-latin-wght.woff2",
  display: "swap",
  variable: "--font-figtree",
  weight: "300 900",
});

export const metadata: Metadata = {
  title: "NextScholar",
  description:
    "Structured mathematics learning for ASEAN Scholarship preparation.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={figtree.variable} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
