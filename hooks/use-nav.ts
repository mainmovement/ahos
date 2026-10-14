'use client';

/**
 * AHOS: nav visibility filter.
 *
 * The ported template implemented this on top of Clerk's client-side RBAC hooks
 * (permissions, plans, org membership). AHOS is a single-operator desktop app
 * with no account directory, so there is nothing to check against: every
 * condition that would have queried Clerk passes, and an item is hidden only if
 * it marks itself `disabled`. The `access` field is kept in the config shape so
 * future multi-operator work can add a real check here without touching
 * `nav-config.ts`.
 */

import { useMemo } from 'react';
import type { NavItem, NavGroup } from '@/types/nav';

function itemVisible(item: NavItem): boolean {
  return !item.disabled && (item.items ? item.items.some(itemVisible) : true);
}

export function useFilteredNavItems(items: NavItem[]): NavItem[] {
  return useMemo(() => items.filter(itemVisible), [items]);
}

export function useFilteredNavGroups(groups: NavGroup[]): NavGroup[] {
  return useMemo(
    () =>
      groups
        .map((group) => ({ ...group, items: group.items.filter(itemVisible) }))
        .filter((group) => group.items.length > 0),
    [groups]
  );
}
