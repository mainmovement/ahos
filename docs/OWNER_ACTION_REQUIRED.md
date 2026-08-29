# AHOS — Owner Action Required (PRE_SOAK)

**STATE B:** never `db:migrate` / `db:push`. Do **not** invent READY.

## Now (Windows laptop `G:\robat\ahos`)

1. Prefer merge **PR #59** (leave **PR #56** OPEN as paste sink).
2. Run:

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/6fd554385bde85a519579cc00a606480da98bae2/AHOS_MAIN_CLEAR_G2.cmd
AHOS_MAIN_CLEAR_G2.cmd
```

3. Paste `reports\OWNER_PASTE_WINDOWS_GATE.txt` into **#56** or **#38**.

**PRE_SOAK** only if Windows report has `pre_soak_entry_ok=true` (G1–G10 PASS).  
**OPERATOR_READY** still needs G11 Telegram E2E.

See also: `reports/OWNER_CARD_WEB_API_AUTH_PRE_SOAK_FA.md`, `OWNER_ONE_LINER.txt`.
