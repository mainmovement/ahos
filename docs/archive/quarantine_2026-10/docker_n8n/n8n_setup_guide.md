# AHOS n8n Production Setup & Workflow Automation Guide

## 1. Overview
AHOS integrates with n8n for scheduled workflow automation, periodic health reports, and event dispatching. All 6 canonical workflows located in `n8n/workflows/` are verified against structural, credential, and security lints.

## 2. Canonical Workflows Catalog
1. `ahos_01_data_ingest_integrity.json`: Triggers periodic observation integrity audits and checks SQLite database health.
2. `ahos_02_signal_pipeline.json`: Automates opportunity candidate scoring and alert dispatching.
3. `ahos_03_telegram_control.json`: Routes Telegram incoming commands toward AHOS.
   **W57 law:** Telegram must not score independently. Production path is
   `Telegram → AHOS_GATEWAY_URL (Conversation Gateway /api/chat) → AHOS Core`.
   Without `AHOS_GATEWAY_URL`, Telegram emits `EMERGENCY_FALLBACK_ONLY`.
   The n8n workflow may still forward messages; it must not invent scores.
4. `ahos_10_research_lab.json`: Executes offline strategy lab backtests and Wilson CI baseline benchmarks.
5. `ahos_11_data_update.json`: Schedules historical data ingestion for research cohorts.
6. `ahos_12_research_report.json`: Formats and exports research summary digests.

## 3. First-Time Setup on Windows 11
1. **Start Services via Docker Desktop:**
   ```powershell
   docker compose -f deployment/docker-compose.windows.yml up -d
   ```
2. **Access n8n Web Interface:**
   Open `http://localhost:5678` in your browser.
3. **Import Workflows:**
   - In the n8n UI, navigate to **Workflows -> Import from File**.
   - Select the JSON workflow files from `n8n/workflows/`.
4. **Configure Credentials:**
   - Add Telegram Bot credential (set Bot Token from `@BotFather`).
   - Add PostgreSQL credential (`host=postgres`, `port=5432`, `database=ahos`).

## 4. Troubleshooting & Maintenance
- **Workflow Execution Failure:** Check n8n execution history tab for node-specific error outputs.
- **Database Connection Error:** Verify PostgreSQL container is healthy via `docker ps`.
- **Workflow Validation:** Run the automated validator at any time:
  ```bash
  python tests/validate_n8n.py
  ```
