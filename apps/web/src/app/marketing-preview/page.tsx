import type { Metadata } from "next";

import { MarketingLanding } from "@/components/marketing/marketing-landing";

export const metadata: Metadata = {
  title: "NextScholar | ASEAN Scholarship preparation",
  description:
    "Structured Mathematics and English learning for secondary students preparing for ASEAN Scholarship selection tests.",
};

export default function MarketingPreviewPage() {
  return (
    <MarketingLanding
      registerHref="/register"
      signInHref="/login?next=%2Flearn"
    />
  );
}
