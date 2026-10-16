import { Suspense } from 'react';

import { NewsroomPage } from '@/features/newsroom/NewsroomPage';

/**
 * The Newsroom screen reads `?demo=1`, `?violation=1`, `?tier=0|1|2`,
 * `?state=…` and `?story=…` from the URL, so it needs a Suspense boundary for
 * `useSearchParams()` to stay statically renderable.
 */
export default function Page() {
  return (
    <Suspense fallback={null}>
      <NewsroomPage />
    </Suspense>
  );
}
