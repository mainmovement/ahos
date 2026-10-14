import { NavGroup } from '@/types/nav';

/**
 * AHOS sidebar navigation (MASTER_SPEC "Layout to match").
 *
 * Ported from the template's Clerk-RBAC nav-config; the `access` field is kept
 * in the shape even though `hooks/use-nav.ts` has no directory to check against
 * yet (single-operator desktop app). Counters come from the live read model, not
 * from here — this file only describes structure.
 *
 * Routes point at AHOS surfaces. Screens that do not exist yet resolve to the
 * section they will live under, so nothing 404s while the shell is being built.
 */
export const navGroups: NavGroup[] = [
  {
    label: 'Command',
    items: [
      {
        title: 'Command Center',
        url: '/',
        icon: 'dashboard',
        isActive: false,
        shortcut: ['d', 'd'],
        items: []
      },
      {
        title: 'Discovery',
        url: '/discovery',
        icon: 'scan',
        isActive: false,
        items: []
      },
      {
        title: 'Opportunities',
        url: '/opportunities',
        icon: 'opportunities',
        isActive: false,
        items: []
      },
      {
        title: 'Market Intelligence',
        url: '/market',
        icon: 'market',
        isActive: false,
        items: []
      }
    ]
  },
  {
    label: 'Intelligence',
    items: [
      {
        title: 'Identity & Security',
        url: '/identity',
        icon: 'security',
        isActive: false,
        items: [
          { title: 'Identity', url: '/identity', icon: 'identity', isActive: false, items: [] },
          { title: 'Security Gate', url: '/security', icon: 'security', isActive: false, items: [] }
        ]
      },
      {
        title: 'Evidence',
        url: '/evidence',
        icon: 'evidence',
        isActive: false,
        items: []
      },
      {
        title: 'Paper Trading',
        url: '/paper',
        icon: 'paperTrading',
        isActive: false,
        items: []
      }
    ]
  },
  {
    label: 'Autonomy',
    items: [
      {
        title: 'Auto Trading (Agents)',
        url: '/agents',
        icon: 'agents',
        isActive: false,
        items: []
      },
      {
        title: 'Chat with AHOS',
        url: '/chat',
        icon: 'chat',
        isActive: false,
        items: []
      }
    ]
  },
  {
    label: 'Knowledge',
    items: [
      {
        title: 'University / Research Lab',
        url: '/university',
        icon: 'university',
        isActive: false,
        items: []
      },
      {
        title: 'Learning',
        url: '/learning',
        icon: 'learning',
        isActive: false,
        items: []
      }
    ]
  },
  {
    label: 'Governance',
    items: [
      {
        title: 'Audit & Governance',
        url: '/audit',
        icon: 'audit',
        isActive: false,
        items: []
      },
      {
        title: 'Settings',
        url: '/settings',
        icon: 'settings',
        isActive: false,
        items: []
      }
    ]
  }
];
