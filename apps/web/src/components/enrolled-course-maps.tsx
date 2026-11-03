"use client";

import { useEffect, useState } from "react";

import { CourseMapPanel } from "@/components/course-map-panel";
import { getProgress, type ProgressResponse } from "@/lib/api/progress";

const FALLBACK_COURSE_KEYS = ["g3-sec1-math"];

/**
 * Shows a course map for each enrolled course on the established learning page.
 * The fixture build has no progress API, so it falls back to the fixture course.
 */
export function EnrolledCourseMaps({
  loadProgress = getProgress,
}: {
  loadProgress?: () => Promise<ProgressResponse>;
}) {
  const [courseKeys, setCourseKeys] = useState<string[] | null>(null);

  useEffect(() => {
    let active = true;
    void loadProgress()
      .then((progress) => {
        if (active) {
          setCourseKeys(progress.courses.map((course) => course.course_key));
        }
      })
      .catch(() => {
        if (active) setCourseKeys(FALLBACK_COURSE_KEYS);
      });
    return () => {
      active = false;
    };
  }, [loadProgress]);

  if (!courseKeys) return null;
  return (
    <>
      {courseKeys.map((courseKey) => (
        <CourseMapPanel courseKey={courseKey} key={courseKey} />
      ))}
    </>
  );
}
