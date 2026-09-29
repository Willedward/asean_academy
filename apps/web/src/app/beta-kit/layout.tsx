import type { Metadata } from "next";
import localFont from "next/font/local";
import { notFound } from "next/navigation";

import "@/beta-kit/kit.css";

const figtree = localFont({
  src: "../../beta-kit/fonts/Figtree-latin-wght.woff2",
  weight: "300 900",
  variable: "--font-figtree",
  display: "swap",
});

export const metadata: Metadata = {
  title: "NextScholar beta kit",
  robots: { index: false, follow: false },
};

/**
 * Design preview for the beta screens. Off in production unless
 * NEXT_PUBLIC_BETA_KIT=true, so it never ships to students by accident.
 */
export default function BetaKitLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_BETA_KIT !== "true") notFound();
  return <div className={`${figtree.variable} font-ns`}>{children}</div>;
}
