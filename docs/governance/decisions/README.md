# M43 Autonomy Tier Governance System

This directory contains the M43 autonomy tier governance system documentation and state files.

## Overview

M43 implements an autonomy tier system for AHOS markets, allowing gradual progression from fully manual (T0) to fully autonomous (T4) operation. Each tier represents a level of operational autonomy with increasing requirements for evidence, signers, and governance.

## System Components

### Core Files

- `../architecture/markets/tier_state.py` - Main tier state implementation
- `../architecture/mission/ledger.py` - Extended with decision support
- `../scripts/m43_tier_state.py` - CLI tool for tier management
- `../tests/test_m43_tier_state.py` - Comprehensive test suite

### State Files

- `AUTONOMY_TIER_CURRENT.md` - Current tier state for all markets

## Tier Structure

| Tier | Autonomy Level | Signers Required | Expiry | Evidence Requirements |
|------|----------------|------------------|---------|---------------------|
| T0   | Fully manual   | 1                | 30 days | PERFORMANCE_T0      |
| T1   | Supervised     | 2                | 60 days | PERFORMANCE_T1, SAFETY_T0 |
| T2   | Semi-autonomous| 3                | 90 days | PERFORMANCE_T2, SAFETY_T1, COMPLIANCE_T1 |
| T3   | Mostly autonomous| 4              | 180 days| PERFORMANCE_T3, SAFETY_T2, COMPLIANCE_T2, GOVERNANCE_T2 |
| T4   | Fully autonomous| 5                | 365 days| PERFORMANCE_T4, SAFETY_T3, COMPLIANCE_T3, GOVERNANCE_T3, AUDIT_T3 |

## Key Concepts

### Decision Records
Each tier promotion creates a decision record with:
- Decision ID (UUID)
- Market identifier
- From/To tiers
- Evidence references
- Signer list
- Authority class
- Creation timestamp

### Evidence Requirements
Each tier requires specific evidence types that must be provided before promotion. Evidence is referenced by kind and validated against the requirements.

### Signer Validation
Promotions require multiple signers based on the target tier. Signers must be properly formatted agent names and cannot be duplicated.

### Expiry Management
Tier decisions have finite expiry periods. After expiry, the market reverts to T0 and must be re-promoted.

## CLI Usage

See `../scripts/m43_tier_state.py` for available commands:

```bash
# Check current tier for a market
python m43_tier_state.py current BTC-USD

# Promote a market to a higher tier
python m43_tier_state.py promote BTC-USD T2 --evidence perf1,safety1 --signers "agent:alice,agent:bob"

# Reject a promotion
python m43_tier_state.py reject BTC-USD "Insufficient evidence"

# List all decisions for a market
python m43_tier_state.py history BTC-USD
```

## Ledger Integration

All tier decisions are recorded as `KIND_DECISION` entries in the mission ledger, providing an immutable audit trail of all tier changes.