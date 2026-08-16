# Contributing to AHOS

Thank you for your interest in contributing to the Artificial Hybrid Opportunity Scoring System.

## Governance & Operating Rules
1. **Never Introduce Live Trading:** AHOS is an intelligence platform and paper-trading laboratory. Pull requests introducing live trade execution or wallet signing will be rejected immediately.
2. **Lane A Immutability:** Historical observation tables and frozen experiment protocols (`docs/mission_v1_1/E01_GATE_PROTOCOL_v1.md`) are immutable. No retroactive backfilling of missed observation windows is permitted.
3. **Evidence > Opinion:** All new features or scoring models must be backed by empirical evidence, reproducible unit tests, and pre-registered hypotheses.
4. **AI is Advisory:** Decision authority belongs exclusively to deterministic algorithms and human operators.

## Development Workflow
1. Fork and clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   ```
3. Run tests before and after changes:
   ```bash
   pytest tests/ -v
   ```
4. Verify code hygiene and security:
   ```bash
   python -m engine.doc_hygiene
   ```
5. Submit a pull request adhering to the 14-stage `improvement_proposal_v1` workflow.
