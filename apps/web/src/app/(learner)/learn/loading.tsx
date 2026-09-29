export default function LearningLoading() {
  return (
    <div
      className="ns-root min-h-dvh bg-ns-surface px-4 py-16 font-ns text-ns-ink"
      role="status"
      aria-label="Loading learning page"
    >
      <div className="mx-auto flex max-w-3xl animate-pulse flex-col gap-5">
        <div className="h-5 w-32 rounded-full bg-ns-line" />
        <div className="h-10 w-3/4 rounded-xl bg-ns-line" />
        <div className="h-44 rounded-2xl bg-ns-brand-soft" />
        <div className="h-72 rounded-2xl bg-ns-line" />
      </div>
    </div>
  );
}
