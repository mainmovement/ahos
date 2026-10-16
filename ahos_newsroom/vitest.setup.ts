import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// `globals` is disabled in vitest.config.ts, so auto-cleanup does not register
// itself: unmount everything after each test to keep the DOM tree isolated.
afterEach(() => {
  cleanup();
});
