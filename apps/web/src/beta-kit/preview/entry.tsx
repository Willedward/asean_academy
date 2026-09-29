import { preview } from "../routes";
import { LandingScreen, OnboardingScreen, SignInScreen, type OnboardingProps } from "../screens/entry";
import type { PreviewEntry } from "./registry";

const onboarding: OnboardingProps = {
  email: "dimas@example.com",
  displayName: "Dimas",
  invitationCode: "NS-7K4Q-2M9X",
  codeFromLink: true,
  tracks: [
    {
      value: "sec3-entry",
      label: "Sec 3 entry",
      description: "You are in Secondary 1 or 2 now.",
    },
    {
      value: "sec1-entry",
      label: "Sec 1 entry",
      description: "You are in Primary 6 now.",
    },
  ],
  selectedTrack: "sec3-entry",
  startingCourse: "Singapore Secondary 1 G3 Mathematics, unit N1 Numbers and their operations.",
  starterPack: {
    welcomeXp: 50,
    firstOutfit: { outfit: "scarf", name: "Batik scarf", level: 3 },
  },
  continueHref: preview("dashboard-new"),
  switchAccountHref: preview("sign-in"),
};

export const entryEntries: PreviewEntry[] = [
  {
    key: "landing",
    title: "Landing",
    group: "Entry",
    canvas: ["Landing.m", "Landing.d"],
    render: () => <LandingScreen betaLabel="Private beta · December 2026" signInHref={preview("sign-in")} />,
  },
  {
    key: "sign-in",
    title: "Sign in",
    group: "Entry",
    canvas: ["SignIn.m"],
    render: () => <SignInScreen error={null} continueHref={preview("onboarding")} landingHref={preview("landing")} />,
  },
  {
    key: "sign-in-error",
    title: "Sign in, error",
    group: "Entry",
    canvas: ["SignIn.d"],
    render: () => (
      <SignInScreen
        error="Sign-in did not finish. Please try again. If it keeps happening, message your NextScholar contact."
        continueHref={preview("onboarding")}
        landingHref={preview("landing")}
      />
    ),
  },
  {
    key: "onboarding",
    title: "Onboarding",
    group: "Entry",
    canvas: ["Onboarding.m", "Onboarding.d"],
    render: () => <OnboardingScreen {...onboarding} />,
  },
  {
    key: "onboarding-error",
    title: "Onboarding, wrong account",
    group: "Entry",
    canvas: ["OnboardingError.m"],
    render: () => (
      <OnboardingScreen
        {...onboarding}
        codeError="This code was sent to a different Google account. Sign in with the email your invitation went to, or ask for a new code."
      />
    ),
  },
];
