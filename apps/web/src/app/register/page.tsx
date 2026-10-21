import type { Metadata } from "next";

import { RegistrationEntry } from "@/components/marketing/registration-entry";

export const metadata: Metadata = {
  title: "Register | NextScholar",
  description:
    "Registration and private-beta access for NextScholar ASEAN Scholarship preparation.",
};

export default function RegisterPage() {
  return <RegistrationEntry />;
}
