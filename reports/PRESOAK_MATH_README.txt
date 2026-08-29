AHOS PRE_SOAK math (simulation only — NOT Windows attestation)
==============================================================
Source paste: evidence branch tip 988edcd / 20260828_220318
host_is_windows=true; G1 PASS; G2 BLOCKED empty gateway; G3-G10 PASS.

Simulation: flip only G2 -> PASS using classify().
Result: pre_soak_entry_ok=true; operator_ready=false (G11 still OWNER_ACTION).

This does NOT invent PRE_SOAK. Owner must re-run on the Windows laptop
(AHOS_MAIN_FIRST.bat) and paste fresh OWNER_PASTE with pre_soak_entry_ok=true.
STATE B: no db:migrate / db:push.
