"""M43 Tier State System Tests

Comprehensive test suite for the autonomy tier state management system.
Tests all core functionality including validation, promotion, rejection,
ledger integration, and edge cases.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock

# Add the project root to sys.path so we can import AHOS modules
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from architecture.mission.ledger import MissionLedger, KIND_DECISION
from architecture.markets.tier_state import (
    DecisionStore, DecisionRecord, TierState, Tier,
)


class TestTierState(unittest.TestCase):
    """Test TierState dataclass functionality."""

    def test_tier_state_creation(self):
        """Test TierState creation and basic properties."""
        market = "BTC-USD"
        tier = Tier.T2

        state = TierState(
            market=market,
            current_tier=tier,
            decision_id="test-decision-id"
        )

        self.assertEqual(state.market, market)
        self.assertEqual(state.current_tier, tier)
        self.assertEqual(state.decision_id, "test-decision-id")
        self.assertIsInstance(state.created_at, str)
        self.assertIsNone(state.expires_at)

    def test_tier_state_expiry_no_expiry(self):
        """Test expiry check when no expiry is set."""
        state = TierState(
            market="BTC-USD",
            current_tier=Tier.T1,
            decision_id="test-id"
        )

        self.assertFalse(state.is_expired())

    def test_tier_state_expiry_valid(self):
        """Test expiry check when expiry is in the future."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        state = TierState(
            market="BTC-USD",
            current_tier=Tier.T1,
            decision_id="test-id",
            expires_at=future_time.isoformat()
        )

        self.assertFalse(state.is_expired())

    def test_tier_state_expiry_expired(self):
        """Test expiry check when expiry is in the past."""
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        state = TierState(
            market="BTC-USD",
            current_tier=Tier.T1,
            decision_id="test-id",
            expires_at=past_time.isoformat()
        )

        self.assertTrue(state.is_expired())

    def test_tier_state_invalid_expiry_format(self):
        """Test expiry check with invalid expiry format."""
        state = TierState(
            market="BTC-USD",
            current_tier=Tier.T1,
            decision_id="test-id",
            expires_at="invalid-timestamp"
        )

        self.assertTrue(state.is_expired())


class TestDecisionRecord(unittest.TestCase):
    """Test DecisionRecord dataclass functionality."""

    def test_decision_record_creation(self):
        """Test DecisionRecord creation with all fields."""
        decision = DecisionRecord(
            decision_id="test-decision-id",
            market="BTC-USD",
            from_tier=Tier.T1,
            to_tier=Tier.T2,
            evidence_refs=["PERFORMANCE_T1", "SAFETY_T0"],
            signers=["agent:alice", "agent:bob"],
            authority="OWNER",
            created_at="2026-10-16T00:00:00.000Z",
            payload={"extra": "data"},
            metadata={"source": "test"}
        )

        self.assertEqual(decision.decision_id, "test-decision-id")
        self.assertEqual(decision.market, "BTC-USD")
        self.assertEqual(decision.from_tier, Tier.T1)
        self.assertEqual(decision.to_tier, Tier.T2)
        self.assertEqual(decision.evidence_refs, ["PERFORMANCE_T1", "SAFETY_T0"])
        self.assertEqual(decision.signers, ["agent:alice", "agent:bob"])
        self.assertEqual(decision.authority, "OWNER")
        self.assertEqual(decision.created_at, "2026-10-16T00:00:00.000Z")
        self.assertEqual(decision.payload, {"extra": "data"})
        self.assertEqual(decision.metadata, {"source": "test"})
        self.assertEqual(decision.signers_rejected, [])

    def test_decision_record_defaults(self):
        """Test DecisionRecord with default values."""
        decision = DecisionRecord(
            decision_id="test-id",
            market="BTC-USD",
            from_tier=Tier.T0,
            to_tier=Tier.T1,
            evidence_refs=[],
            signers=[]
        )

        self.assertEqual(decision.signers_rejected, [])
        self.assertEqual(decision.payload, {})
        self.assertEqual(decision.metadata, {})
        self.assertIsInstance(decision.created_at, str)


class TestDecisionStore(unittest.TestCase):
    """Test DecisionStore functionality with mocked ledger."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_ledger = MagicMock()
        self.store = DecisionStore(self.mock_ledger)
        self.test_market = "BTC-USD"

    def test_record_decision(self):
        """Test decision recording to ledger."""
        decision = DecisionRecord(
            decision_id="test-id",
            market=self.test_market,
            from_tier=Tier.T0,
            to_tier=Tier.T1,
            evidence_refs=["PERFORMANCE_T0"],
            signers=["agent:alice"]
        )

        # Mock the ledger.decision method to return a real dict
        mock_result = {
            "kind": KIND_DECISION,
            "payload": {
                "decision_id": "test-id",
                "market": self.test_market,
                "from_tier": "T0",
                "to_tier": "T1",
                "evidence_refs": ["PERFORMANCE_T0"],
                "signers": ["agent:alice"],
                "signers_rejected": [],
                "authority": "NONE",
                "created_at": decision.created_at,
                "metadata": {},
                "payload": {}
            },
            "seq": 1,
            "ts": "2026-10-16T00:00:00.000000Z",
            "entry_hash": "0" * 64
        }

        self.mock_ledger.decision.return_value = mock_result
        self.mock_ledger.current_decision.return_value = None
        self.mock_ledger.decision_history.return_value = []

        result = self.store.record(decision)

        # Verify ledger.decision was called
        self.mock_ledger.decision.assert_called_once()

        # Verify result
        self.assertIsInstance(result, dict)
        self.assertEqual(result["kind"], KIND_DECISION)

    def test_promote_t0_to_t1(self):
        """Test promoting from T0 to T1."""
        self.mock_ledger.current_decision.return_value = None
        self.mock_ledger.decision.return_value = {"kind": KIND_DECISION}

        # T1 promotion requires at least 2 signers
        decision = self.store.promote(
            market=self.test_market,
            to_tier=Tier.T1,
            evidence_refs=["PERFORMANCE_T0"],  # Correct evidence kind
            signers=["agent:alice", "agent:bob"]
        )

        self.assertEqual(decision.market, self.test_market)
        self.assertEqual(decision.from_tier, Tier.T0)
        self.assertEqual(decision.to_tier, Tier.T1)
        self.assertEqual(decision.evidence_refs, ["PERFORMANCE_T0"])
        self.assertEqual(decision.signers, ["agent:alice", "agent:bob"])

        # Verify cache was updated
        cached = self.store._cache[self.test_market]
        self.assertEqual(cached.current_tier, Tier.T1)
        self.assertIsNotNone(cached.expires_at)

    def test_promote_t0_to_t2(self):
        """Test promoting from T0 to T2 with proper evidence."""
        self.mock_ledger.current_decision.return_value = None
        self.mock_ledger.decision.return_value = {"kind": KIND_DECISION}

        # T1 promotion requires at least 2 signers, T2 requires at least 3
        decision = self.store.promote(
            market=self.test_market,
            to_tier=Tier.T2,
            evidence_refs=["PERFORMANCE_T0"],  # Evidence for T0->T1 (base requirement)
            signers=["agent:alice", "agent:bob", "agent:charlie"]
        )

        self.assertEqual(decision.market, self.test_market)
        self.assertEqual(decision.from_tier, Tier.T0)
        self.assertEqual(decision.to_tier, Tier.T2)
        self.assertEqual(decision.evidence_refs, ["PERFORMANCE_T0"])
        self.assertEqual(decision.signers, ["agent:alice", "agent:bob", "agent:charlie"])

    def test_promote_t1_to_t2(self):
        """Test promoting from T1 to T2 with proper evidence."""
        # Set current tier to T1 by providing a mock current decision
        mock_payload = {
            "decision_id": "test-current-id",
            "market": self.test_market,
            "from_tier": "T0",
            "to_tier": "T1",
            "evidence_refs": ["PERFORMANCE"],
            "signers": ["agent:alice", "agent:bob"],
            "authority": "OWNER",
            "created_at": "2026-10-16T00:00:00.000Z"
        }

        mock_entry = {
            "kind": KIND_DECISION,
            "payload": mock_payload,
            "seq": 1,
            "ts": "2026-10-16T00:00:00.000000Z",
            "entry_hash": "0" * 64
        }

        self.mock_ledger.current_decision.return_value = mock_entry
        self.mock_ledger.decision.return_value = {"kind": KIND_DECISION}

        # T2 promotion requires at least 3 signers and proper evidence
        decision = self.store.promote(
            market=self.test_market,
            to_tier=Tier.T2,
            evidence_refs=["PERFORMANCE_T1", "SAFETY_T0"],  # Evidence for T1->T2
            signers=["agent:alice", "agent:bob", "agent:charlie"]
        )

        self.assertEqual(decision.market, self.test_market)
        self.assertEqual(decision.from_tier, Tier.T1)
        self.assertEqual(decision.to_tier, Tier.T2)
        self.assertEqual(decision.evidence_refs, ["PERFORMANCE_T1", "SAFETY_T0"])
        self.assertEqual(decision.signers, ["agent:alice", "agent:bob", "agent:charlie"])

    def test_promote_downward_fails(self):
        """Test that downward promotion fails."""
        self.mock_ledger.current_decision.return_value = None

        with self.assertRaises(ValueError) as cm:
            self.store.promote(
                market=self.test_market,
                to_tier=Tier.T0,
                evidence_refs=["PERFORMANCE_T0"],
                signers=["agent:alice"]
            )

        self.assertIn("Cannot promote", str(cm.exception))

    def test_promote_same_tier_fails(self):
        """Test that promoting to the same tier fails."""
        self.mock_ledger.current_decision.return_value = None
        self.mock_ledger.decision.return_value = {"kind": KIND_DECISION}

        # First promote to T1
        self.store.promote(
            market=self.test_market,
            to_tier=Tier.T1,
            evidence_refs=["PERFORMANCE_T0"],
            signers=["agent:alice", "agent:bob"]
        )

        # Now try to promote from T1 to T1 (same tier)
        with self.assertRaises(ValueError) as cm:
            self.store.promote(
                market=self.test_market,
                to_tier=Tier.T1,
                evidence_refs=["PERFORMANCE_T0"],
                signers=["agent:alice", "agent:bob"]
            )

        self.assertIn("Cannot promote", str(cm.exception))

    def test_promote_insufficient_evidence_fails(self):
        """Test that promotion with insufficient evidence fails."""
        self.mock_ledger.current_decision.return_value = None

        with self.assertRaises(ValueError) as cm:
            self.store.promote(
                market=self.test_market,
                to_tier=Tier.T2,
                evidence_refs=["PERFORMANCE_T1"],  # Missing SAFETY_T0
                signers=["agent:alice", "agent:bob", "agent:charlie"]
            )

        self.assertIn("Missing required evidence", str(cm.exception))

    def test_promote_insufficient_signers_fails(self):
        """Test that promotion with insufficient signers fails."""
        self.mock_ledger.current_decision.return_value = None

        with self.assertRaises(ValueError) as cm:
            self.store.promote(
                market=self.test_market,
                to_tier=Tier.T2,
                evidence_refs=["PERFORMANCE_T1", "SAFETY_T0"],
                signers=["agent:alice"]  # Need at least 3 signers for T2
            )

        self.assertIn("Need at least", str(cm.exception))

    def test_promote_duplicate_signers_fails(self):
        """Test that promotion with duplicate signers fails."""
        self.mock_ledger.current_decision.return_value = None

        with self.assertRaises(ValueError) as cm:
            self.store.promote(
                market=self.test_market,
                to_tier=Tier.T1,
                evidence_refs=["PERFORMANCE_T0"],
                signers=["agent:alice", "agent:alice"]  # Duplicate
            )

        self.assertIn("Duplicate signers", str(cm.exception))

    def test_current_tier_no_decision(self):
        """Test current tier when no decision exists."""
        self.mock_ledger.current_decision.return_value = None

        tier = self.store.current_tier(self.test_market)
        self.assertEqual(tier, Tier.T0)  # Default

    def test_current_tier_with_decision(self):
        """Test current tier with existing decision."""
        mock_payload = {
            "decision_id": "test-id",
            "market": self.test_market,
            "from_tier": "T1",
            "to_tier": "T2",
            "evidence_refs": ["PERFORMANCE_T1", "SAFETY_T0"],
            "signers": ["agent:alice", "agent:bob"],
            "authority": "OWNER",
            "created_at": "2026-10-16T00:00:00.000Z"
        }

        mock_entry = {
            "kind": KIND_DECISION,
            "payload": mock_payload,
            "seq": 1,
            "ts": "2026-10-16T00:00:00.000000Z",
            "entry_hash": "0" * 64
        }

        self.mock_ledger.current_decision.return_value = mock_entry

        tier = self.store.current_tier(self.test_market)
        self.assertEqual(tier, Tier.T2)

    def test_check_expiry_no_decision(self):
        """Test expiry check when no decision exists."""
        self.mock_ledger.current_decision.return_value = None

        result = self.store.check_expiry(self.test_market)
        self.assertTrue(result)  # No decision means needs re-promotion

    def test_check_expiry_with_decision(self):
        """Test expiry check with existing decision."""
        # Mock non-expired decision
        mock_payload = {
            "decision_id": "test-id",
            "market": self.test_market,
            "from_tier": "T1",
            "to_tier": "T2",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        }

        mock_entry = {
            "kind": KIND_DECISION,
            "payload": mock_payload,
            "seq": 1,
            "ts": "2026-10-16T00:00:00.000000Z",
            "entry_hash": "0" * 64
        }

        self.mock_ledger.current_decision.return_value = mock_entry

        result = self.store.check_expiry(self.test_market)
        self.assertFalse(result)  # Not expired yet

    def test_reject_skip(self):
        """Test rejecting a promotion attempt."""
        mock_entry = {
            "kind": KIND_DECISION,
            "payload": {
                "decision_id": "test-id",
                "market": self.test_market,
                "from_tier": "T0",
                "to_tier": "T0"
            },
            "seq": 1,
            "ts": "2026-10-16T00:00:00.000000Z",
            "entry_hash": "0" * 64
        }

        self.mock_ledger.current_decision.return_value = mock_entry
        self.mock_ledger.decision.return_value = {"kind": KIND_DECISION}

        decision = self.store.reject_skip(
            market=self.test_market,
            reason="Insufficient evidence"
        )

        # Verify ledger.decision was called
        self.mock_ledger.decision.assert_called()

        # Verify the decision has reject characteristics
        call_args = self.mock_ledger.decision.call_args[0][0]
        payload = call_args

        self.assertEqual(payload["authority"], "REJECT_SKIP")
        self.assertEqual(payload["payload"]["reject_reason"], "Insufficient evidence")

    def test_get_decision_history(self):
        """Test getting decision history for a market."""
        mock_entries = [
            {
                "kind": KIND_DECISION,
                "payload": {"market": "BTC-USD", "decision_id": "id1"},
                "seq": 1,
                "ts": "2026-10-16T00:00:00.000000Z",
                "entry_hash": "0" * 64
            },
            {
                "kind": KIND_DECISION,
                "payload": {"market": "ETH-USD", "decision_id": "id2"},
                "seq": 2,
                "ts": "2026-10-16T00:00:00.000000Z",
                "entry_hash": "0" * 64
            },
            {
                "kind": KIND_DECISION,
                "payload": {"market": "BTC-USD", "decision_id": "id3"},
                "seq": 3,
                "ts": "2026-10-16T00:00:00.000000Z",
                "entry_hash": "0" * 64
            }
        ]

        self.mock_ledger.decision_history.return_value = mock_entries

        history = self.store.get_decision_history(self.test_market)

        self.assertEqual(len(history), 2)  # Only BTC-USD entries
        self.assertEqual(history[0]["payload"]["decision_id"], "id1")
        self.assertEqual(history[1]["payload"]["decision_id"], "id3")


class TestValidationHelpers(unittest.TestCase):
    """Test validation helper functions."""

    def test_validate_signers_t0(self):
        """Test signer validation for T0."""
        from architecture.markets.tier_state import DecisionStore

        mock_ledger = MagicMock()
        store = DecisionStore(mock_ledger)

        # T0 requires at least 1 signer
        store.validate_signers(["agent:alice"], Tier.T0)
        store.validate_signers(["agent:alice", "agent:bob"], Tier.T0)  # More is OK

    def test_validate_signers_t4(self):
        """Test signer validation for T4."""
        from architecture.markets.tier_state import DecisionStore

        mock_ledger = MagicMock()
        store = DecisionStore(mock_ledger)

        # T4 requires exactly 5 signers
        store.validate_signers(["agent:a1", "agent:a2", "agent:a3", "agent:a4", "agent:a5"], Tier.T4)

        with self.assertRaises(ValueError):
            store.validate_signers(["agent:a1", "agent:a2", "agent:a3", "agent:a4"], Tier.T4)  # Too few

    def test_validate_signers_invalid_format(self):
        """Test validation with invalid signer format."""
        from architecture.markets.tier_state import DecisionStore
        from architecture.mission.ledger import LedgerError

        mock_ledger = MagicMock()
        store = DecisionStore(mock_ledger)

        with self.assertRaises((ValueError, LedgerError)):
            store.validate_signers("not-a-list", Tier.T1)

        with self.assertRaises(LedgerError):
            store.validate_signers(["alice", "agent:bob"], Tier.T1)  # Invalid format


class TestConstants(unittest.TestCase):
    """Test constant definitions."""

    def test_signers_per_tier(self):
        """Test signer count per tier."""
        from architecture.markets.tier_state import SIGNERS_PER_TIER
        self.assertEqual(SIGNERS_PER_TIER[Tier.T0], 1)
        self.assertEqual(SIGNERS_PER_TIER[Tier.T1], 2)
        self.assertEqual(SIGNERS_PER_TIER[Tier.T2], 3)
        self.assertEqual(SIGNERS_PER_TIER[Tier.T3], 4)
        self.assertEqual(SIGNERS_PER_TIER[Tier.T4], 5)

    def test_tier_expiry_days(self):
        """Test expiry durations per tier."""
        from architecture.markets.tier_state import TIER_EXPIRY_DAYS
        self.assertEqual(TIER_EXPIRY_DAYS[Tier.T0], 30)
        self.assertEqual(TIER_EXPIRY_DAYS[Tier.T1], 60)
        self.assertEqual(TIER_EXPIRY_DAYS[Tier.T2], 90)
        self.assertEqual(TIER_EXPIRY_DAYS[Tier.T3], 180)
        self.assertEqual(TIER_EXPIRY_DAYS[Tier.T4], 365)


class TestIntegration(unittest.TestCase):
    """Integration tests with real ledger."""

    def setUp(self):
        """Set up integration test with temporary ledger."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.ledger_path = Path(self.temp_dir) / "test_ledger.jsonl"

        # Create real ledger
        self.ledger = MissionLedger(self.ledger_path)
        self.store = DecisionStore(self.ledger)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_full_promotion_workflow(self):
        """Test complete promotion workflow with real ledger."""
        market = "BTC-USD"

        # Promote T0 -> T1 (requires 2 signers)
        decision1 = self.store.promote(
            market=market,
            to_tier=Tier.T1,
            evidence_refs=["PERFORMANCE_T0"],
            signers=["agent:alice", "agent:bob"],
            authority="OWNER"
        )

        # Verify ledger entry
        entries = self.ledger.entries()
        decision_entries = [e for e in entries if e.get("kind") == KIND_DECISION]
        self.assertEqual(len(decision_entries), 1)

        # Check current tier
        current = self.store.current_tier(market)
        self.assertEqual(current, Tier.T1)

        # Check cache
        cached = self.store._cache[market]
        self.assertEqual(cached.current_tier, Tier.T1)
        self.assertIsNotNone(cached.expires_at)

        # Promote T1 -> T2 (provide evidence for T1, not T2)
        decision2 = self.store.promote(
            market=market,
            to_tier=Tier.T2,
            evidence_refs=["PERFORMANCE_T1", "SAFETY_T0"],
            signers=["agent:alice", "agent:bob", "agent:charlie"],
            authority="GOVERNANCE"
        )

        # Verify second entry
        decision_entries = [e for e in self.ledger.entries() if e.get("kind") == KIND_DECISION]
        self.assertEqual(len(decision_entries), 2)

        # Check current tier again
        current = self.store.current_tier(market)
        self.assertEqual(current, Tier.T2)

        # Check decision history
        history = self.store.get_decision_history(market)
        self.assertEqual(len(history), 2)

        # Check expiry
        is_expired = self.store.check_expiry(market)
        self.assertFalse(is_expired)  # Should not be expired right after promotion


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
