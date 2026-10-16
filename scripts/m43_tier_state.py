"""M43 Tier State CLI Tool

Command-line interface for managing autonomy tier states for AHOS markets.
Provides commands for checking current tiers, promoting markets, rejecting promotions,
and viewing decision history.

Usage:
    python m43_tier_state.py current <market>
    python m43_tier_state.py promote <market> <tier> --evidence <refs> --signers <agents> [--authority <class>]
    python m43_tier_state.py reject <market> <reason>
    python m43_tier_state.py history <market>
    python m43_tier_state.py expiry <market>
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Add the project root to sys.path so we can import AHOS modules
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from architecture.mission.ledger import MissionLedger
from architecture.markets.tier_state import DecisionStore, Tier


def get_ledger() -> MissionLedger:
    """Get the mission ledger instance."""
    # Try to import config for data directory
    try:
        from config.paths import get_data_dir
        base = Path(get_data_dir())
    except ImportError:
        # Fallback to relative path
        base = project_root / "data"

    ledger_path = base / "mission_ledger" / "mission_ledger.jsonl"
    return MissionLedger(ledger_path)


def get_store() -> DecisionStore:
    """Get the decision store instance."""
    ledger = get_ledger()
    return DecisionStore(ledger)


def current_tier_command(args: argparse.Namespace) -> None:
    """Show current tier for a market."""
    store = get_store()
    try:
        tier = store.current_tier(args.market)
        state = store._cache.get(args.market)

        print(f"## {args.market}")
        print(f"- **Current Tier**: {tier.value}")
        print(f"- **Decision ID**: {state.decision_id if state else 'N/A'}")
        print(f"- **Created**: {state.created_at if state else 'N/A'}")
        print(f"- **Expires**: {state.expires_at if state else 'N/A'}")

        if state and state.is_expired():
            print("- **Status**: ⚠️ EXPIRED")
        else:
            print("- **Status**: ✅ Valid")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def promote_command(args: argparse.Namespace) -> None:
    """Promote a market to a higher tier."""
    store = get_store()

    try:
        # Parse evidence refs
        evidence_refs = args.evidence.split(",") if args.evidence else []

        # Parse signers
        signers = args.signers.split(",") if args.signers else []

        # Parse authority
        authority = args.authority or "NONE"

        # Get target tier
        target_tier = Tier(args.tier.upper())

        print(f"Promoting {args.market} to {target_tier.value}...")
        print(f"Evidence: {evidence_refs}")
        print(f"Signers: {signers}")
        print(f"Authority: {authority}")

        # Perform promotion
        decision = store.promote(
            market=args.market,
            to_tier=target_tier,
            evidence_refs=evidence_refs,
            signers=signers,
            authority=authority,
            metadata={"cli_command": True}
        )

        print(f"✅ Promotion successful!")
        print(f"Decision ID: {decision.decision_id}")
        print(f"Recorded in ledger at entry: {decision.get('seq', 'N/A')}")

        # Update current tier file
        update_current_file(args.market, target_tier, decision.decision_id)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def reject_command(args: argparse.Namespace) -> None:
    """Reject a promotion attempt."""
    store = get_store()

    try:
        print(f"Rejecting promotion for {args.market}...")
        print(f"Reason: {args.reason}")

        # Perform rejection
        decision = store.reject_skip(args.market, args.reason)

        print(f"✅ Rejection recorded!")
        print(f"Decision ID: {decision.get('payload', {}).get('decision_id', 'N/A')}")
        print(f"Recorded in ledger at entry: {decision.get('seq', 'N/A')}")

        # Update current tier file (no change)
        current_tier = store.current_tier(args.market)
        update_current_file(args.market, current_tier, "N/A", reject_reason=args.reason)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def history_command(args: argparse.Namespace) -> None:
    """Show decision history for a market."""
    store = get_store()

    try:
        decisions = store.get_decision_history(args.market)

        if not decisions:
            print(f"No decision history found for {args.market}")
            return

        print(f"## Decision History: {args.market}")
        print()

        for i, decision in enumerate(decisions, 1):
            payload = decision.get("payload", {})

            print(f"### Decision #{i}")
            print(f"- **ID**: {payload.get('decision_id', 'N/A')}")
            print(f"- **From**: {payload.get('from_tier', 'N/A')}")
            print(f"- **To**: {payload.get('to_tier', 'N/A')}")
            print(f"- **Created**: {payload.get('created_at', 'N/A')}")
            print(f"- **Authority**: {payload.get('authority', 'N/A')}")

            evidence = payload.get('evidence_refs', [])
            if evidence:
                print(f"- **Evidence**: {', '.join(evidence)}")

            signers = payload.get('signers', [])
            if signers:
                print(f"- **Signers**: {', '.join(signers)}")

            signers_rejected = payload.get('signers_rejected', [])
            if signers_rejected:
                print(f"- **Rejected Signers**: {', '.join(signers_rejected)}")

            reject_reason = payload.get('reject_reason')
            if reject_reason:
                print(f"- **Reject Reason**: {reject_reason}")

            print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def expiry_command(args: argparse.Namespace) -> None:
    """Check expiry status for a market."""
    store = get_store()

    try:
        is_expired = store.check_expiry(args.market)
        current_tier = store.current_tier(args.market)

        print(f"## {args.market}")
        print(f"- **Current Tier**: {current_tier.value}")
        print(f"- **Status**: {'⚠️ EXPIRED' if is_expired else '✅ Valid'}")

        if not is_expired:
            cached = store._cache.get(args.market)
            if cached and cached.expires_at:
                print(f"- **Expires**: {cached.expires_at}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def update_current_file(market: str, tier: Tier, decision_id: str, reject_reason: Optional[str] = None) -> None:
    """Update the current tier state file."""
    docs_dir = project_root / "docs" / "governance" / "decisions"
    current_file = docs_dir / "AUTONOMY_TIER_CURRENT.md"

    # Read existing content
    try:
        with open(current_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = """# Current Autonomy Tier State

This file documents the current autonomy tier status for all AHOS markets.

## Format

Each market entry follows this structure:

```markdown
## [MARKET-IDENTIFIER]

- **Current Tier**: [T0-T4]
- **Decision ID**: [UUID]
- **Created**: [ISO timestamp]
- **Expires**: [ISO timestamp or "N/A"]
- **Last Updated**: [ISO timestamp]
```

## Markets

<!-- This file is automatically generated by tier management commands -->

*No markets have been assigned to tiers yet.*

---
**Generated**: 2026-10-16T00:00:00.000Z
**Updated**: Manual updates via tier promotion commands
**Maintained**: Tier State Management System
"""

    # Find or create market entry
    lines = content.split('\n')
    market_start = None
    market_end = None

    for i, line in enumerate(lines):
        if line == f"## {market}":
            market_start = i
        elif market_start is not None and line.startswith("## ") and line != f"## {market}":
            market_end = i
            break

    # Create new market entry
    new_entry = [
        f"## {market}",
        f"- **Current Tier**: {tier.value}",
        f"- **Decision ID**: {decision_id}",
        f"- **Created**: {datetime.now(timezone.utc).isoformat()}",
        f"- **Expires**: N/A",
        f"- **Last Updated**: {datetime.now(timezone.utc).isoformat()}",
    ]

    if reject_reason:
        new_entry.append(f"- **Reject Reason**: {reject_reason}")

    # Replace or add market entry
    if market_start is not None:
        if market_end is None:
            lines = lines[:market_start] + new_entry
        else:
            lines = lines[:market_start] + new_entry + lines[market_end:]
    else:
        # Find insertion point (after "## Markets" section)
        insert_pos = None
        for i, line in enumerate(lines):
            if line == "## Markets":
                insert_pos = i + 1
                break

        if insert_pos:
            lines = lines[:insert_pos] + new_entry + [""] + lines[insert_pos:]
        else:
            lines += [""] + new_entry

    # Update header
    for i, line in enumerate(lines):
        if line.startswith("**Generated**"):
            lines[i] = f"**Generated**: {datetime.now(timezone.utc).isoformat()}"
            break

    # Write back
    with open(current_file, 'w') as f:
        f.write('\n'.join(lines))


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="M43 Tier State CLI Tool",
        epilog="For more information, see docs/governance/decisions/README.md"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Current command
    current_parser = subparsers.add_parser('current', help='Show current tier for a market')
    current_parser.add_argument('market', help='Market identifier (e.g., BTC-USD)')

    # Promote command
    promote_parser = subparsers.add_parser('promote', help='Promote a market to a higher tier')
    promote_parser.add_argument('market', help='Market identifier')
    promote_parser.add_argument('tier', help='Target tier (T0-T4)')
    promote_parser.add_argument('--evidence', help='Comma-separated evidence references')
    promote_parser.add_argument('--signers', help='Comma-separated signer agent names')
    promote_parser.add_argument('--authority', default='NONE', help='Authority class')

    # Reject command
    reject_parser = subparsers.add_parser('reject', help='Reject a promotion attempt')
    reject_parser.add_argument('market', help='Market identifier')
    reject_parser.add_argument('reason', help='Reason for rejection')

    # History command
    history_parser = subparsers.add_parser('history', help='Show decision history for a market')
    history_parser.add_argument('market', help='Market identifier')

    # Expiry command
    expiry_parser = subparsers.add_parser('expiry', help='Check expiry status for a market')
    expiry_parser.add_argument('market', help='Market identifier')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)


    # Dispatch commands
    if args.command == 'current':
        current_tier_command(args)
    elif args.command == 'promote':
        promote_command(args)
    elif args.command == 'reject':
        reject_command(args)
    elif args.command == 'history':
        history_command(args)
    elif args.command == 'expiry':
        expiry_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()