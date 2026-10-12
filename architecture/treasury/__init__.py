"""Treasury controls (vision §7): the single-ledger reconcile and the two
surveillance checks that can stop the system.

M42 lives here: the nightly counterparty reconcile over the single hash-chained
ledger (``reconcile``), and the broker-concentration and USDT-depeg checks the
vision makes halt-capable (``surveillance``).

PAPER_ONLY. The treasury never holds a key, never moves funds and never closes
a position. It *reports* — a mismatch is a HALT recorded on the chain — and the
callers that read ``MissionLedger.halted()`` are what gives the record its
effect. Real custody is owner-act (§7.0: "the system builds a withdrawal
*request* and the owner executes it manually").
"""
