import type { Href, NavKey } from "./types";

/**
 * Where kit links point. The preview route uses PREVIEW_ROUTES so every
 * screen links to another preview screen. In the real app, pass your own
 * routes (for example `{ ...PREVIEW_ROUTES, learn: "/learn" }`) to the shells
 * and screens that accept a `routes` prop.
 */
export interface KitRoutes {
  nav: Record<NavKey, Href>;
  streak: Href;
  quests: Href;
  league: Href;
  profile: Href;
  badges: Href;
  settings: Href;
  review: Href;
}

export const preview = (screen: string): Href => `/beta-kit/${screen}`;

export const PREVIEW_ROUTES: KitRoutes = {
  nav: {
    learn: preview("dashboard"),
    course: preview("course-map"),
    league: preview("league"),
    progress: preview("progress"),
    me: preview("me"),
  },
  streak: preview("streak"),
  quests: preview("quests"),
  league: preview("league"),
  profile: preview("me"),
  badges: preview("badges"),
  settings: preview("settings"),
  review: preview("review"),
};
