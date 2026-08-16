# Security Policy for AHOS

## 1. Zero Credential Storage Policy
AHOS strictly adheres to a zero-secret-in-source policy:
- No API keys, Telegram Bot tokens, private keys, or passwords may ever be committed to the repository.
- Sensitive environment variables are injected exclusively via `.env` files (gitignored).
- All structured loggers and exception handlers automatically sanitize output using `architecture.security.sanitize_secrets`.

## 2. Hard Security Vetoes
The opportunity scoring engine enforces non-negotiable security vetoes:
- **Honeypot Veto:** Any token flagged as a honeypot receives an immediate opportunity score of 0.0 and a `CRITICAL` risk classification.
- **Authority Veto:** Tokens retaining active, unrenounced mint or freeze authority receive severe risk penalties.
- **Concentration Veto:** Top-10 holder concentration exceeding 70% triggers high-risk alerts.

## 3. Reporting a Vulnerability
If you discover a security vulnerability, please do NOT open a public issue. Submit an encrypted security advisory to the Lead Architect or email the project security contact.
