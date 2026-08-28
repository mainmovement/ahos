# Windows gate evidence inbox

This PR head (`cursor/windows-evidence-inbox-4bde`) stays open so laptop
`scripts/windows_push_gate_evidence.ps1` can notify via `gh pr comment` when a
new OWNER_PASTE / gate JSON is pushed to `cursor/windows-gate-evidence-4bde`.

- Not an OPERATOR_READY / PRE_SOAK claim by itself
- STATE B: never db:migrate / db:push
- Agent: on comment, fetch `origin/cursor/windows-gate-evidence-4bde` and read
  `reports/windows_gate_evidence/`; honor `pre_soak_entry_ok` only from Windows paste

Owner one-click:

```bat
cd /d G:\robat\ahos
git pull origin main
AHOS_PRE_SOAK_NOW.bat
```

## Keep open

PR head `cursor/windows-evidence-inbox-open-4bde` is the durable open sink.
Do not merge unless replacing with a newer open inbox head. Merging #50 closed
the first inbox; this head restores an open notify target.
