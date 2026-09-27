import { Captions, Video } from "lucide-react";

export function LessonMediaPanel() {
  return (
    <section
      className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6 sm:p-8"
      aria-labelledby="video-lesson-title"
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <div className="flex aspect-video w-full max-w-xs items-center justify-center rounded-2xl bg-slate-900 text-white">
          <Video aria-hidden="true" className="size-10" />
        </div>
        <div>
          <p className="mb-1 text-xs font-extrabold uppercase tracking-[0.12em] text-amber-700">
            Video pending
          </p>
          <h2 id="video-lesson-title" className="my-0 text-2xl font-extrabold">
            Video lesson will be added here
          </h2>
          <p className="mb-3 leading-7 text-slate-600">
            The complete written lesson is available below, so the video is not required to continue this draft lesson.
          </p>
          <p className="m-0 inline-flex items-center gap-2 text-sm font-semibold text-slate-600">
            <Captions aria-hidden="true" className="size-4" />
            Captions and a transcript will be required with the final video.
          </p>
        </div>
      </div>
    </section>
  );
}
