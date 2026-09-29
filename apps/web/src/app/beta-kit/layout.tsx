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
 * Design preview for the beta screens. In production, the request proxy
 * returns 404 unless the deployment is built with NEXT_PUBLIC_BETA_KIT=true.
 */
export default function BetaKitLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_BETA_KIT !== "true") notFound();
  return <div className={`${figtree.variable} font-ns`}>{children}</div>;
}
