'use client';
import React from 'react';
import { ActiveThemeProvider } from '@/components/themes/active-theme';

/**
 * AHOS: no ClerkProvider and no React-Query provider. Authentication is the
 * launcher's one-time bootstrap token → local session (app/api/auth/session,
 * chat_auth.ts); the shell holds no remote account. Nothing in AHOS uses React
 * Query — the overview polls `/api/command` with its own hook — so the ported
 * template's query provider was dead weight pulling an uninstalled package.
 */
export default function Providers({
  activeThemeValue,
  children
}: {
  activeThemeValue: string;
  children: React.ReactNode;
}) {
  return (
    <ActiveThemeProvider initialTheme={activeThemeValue}>
      {children}
    </ActiveThemeProvider>
  );
}
