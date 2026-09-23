import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-5">
      <p className="font-bold text-teal-700">404</p>
      <h1 className="text-3xl font-black">Page not found</h1>
      <p className="text-slate-600">The requested learning page does not exist yet.</p>
      <Link className="font-semibold underline" href="/">Return to the foundation screen</Link>
    </main>
  );
}
