"""M37 locked frontier slots."""
import pytest

from architecture.ai.frontier_slots import LOCKED, OPEN, FrontierSlot, OrderPathError, choose_slot


def test_locked_slot_is_skipped_and_order_path_raises():
    slots = (
        FrontierSlot("gpt-6-astra", LOCKED, 0.0),
        FrontierSlot("argon", OPEN, 1.0),
        FrontierSlot("local", OPEN, 0.2),
    )
    chosen = choose_slot(slots, purpose="council")
    assert chosen is not None
    assert chosen.name == "local"
    with pytest.raises(OrderPathError):
        choose_slot(slots, purpose="order")
