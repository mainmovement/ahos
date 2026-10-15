import { AhosShell } from '@/components/shell/AhosShell';

export const dynamic = 'force-dynamic';

/**
 * Honest placeholder for unbuilt surfaces.
 *
 * The sidebar (owner reference 01) lists all fifteen sections, but only the
 * command center (`/`), `/badge_sheet`, and `/command_center` have pages yet.
 * Rather than 404 — or worse, fabricate an empty-looking dashboard behind every
 * link — every unbuilt route resolves here and says exactly that: NOT_STARTED,
 * root\\_branch only. Next.js matches concrete segments before a catch-all, so
 * the moment a real `app/<section>/page.tsx` exists it takes over and this page
 * stops serving for that path. Nothing here is data: it is a receipt for absent
 * work, which is why no number, chart, or count appears on it.
 */
export default async function SurfacePlaceholder({
  params
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  const path = '/' + slug.join('/');

  return (
    <AhosShell>
      <main className='flex min-h-svh flex-col items-center justify-center gap-6 p-8 text-center'>
        <h1 className='font-[var(--font-orbitron)] text-2xl font-bold tracking-wide text-foreground md:text-3xl'>
          این بخش هنوز ساخته نشده است
        </h1>
        <p className='text-sm text-muted-foreground md:text-base'>
          This surface is <span className='font-mono'>NOT_STARTED</span> — no
          read model, no evidence, and no UI exists for it yet.
        </p>
        <p className='rounded-md border border-border bg-muted/40 px-4 py-2 font-mono text-xs text-muted-foreground md:text-sm'>
          {path}
        </p>
        <p className='max-w-md text-xs text-muted-foreground'>
          این مسیر به بخشی ختم می‌شود که هنوز پیاده‌سازی نشده. هیچ داده‌ای برای
          نمایش وجود ندارد تا ساختار آن آماده شود.
        </p>
      </main>
    </AhosShell>
  );
}
