import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <Link href="/orb-demo" className="rounded border border-amber-400/40 px-4 py-2 text-amber-200 hover:bg-amber-400/10">
        Demo / دمو
      </Link>
    </main>
  );
}