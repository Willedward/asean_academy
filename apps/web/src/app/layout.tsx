import type { Metadata } from "next";

import "katex/dist/katex.min.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "ASEAN Academy",
  description: "Course-led preparation for ASEAN scholarship candidates.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
