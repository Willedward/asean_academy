import localFont from "next/font/local";

const figtree = localFont({
  src: "../../beta-kit/fonts/Figtree-latin-wght.woff2",
  display: "swap",
  variable: "--font-figtree",
  weight: "300 900",
});

export default async function LearnerLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <div className={figtree.variable}>{children}</div>;
}
