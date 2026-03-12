# 🩺 Doctor AI Infra

[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?logo=react)](https://reactjs.org/)
[![Protocol: Antigravity](https://img.shields.io/badge/Protocol-Antigravity-orange.svg)]()

> A secure, monorepo-style infrastructure for the **Doctor AI** network, featuring a robust backend, modern frontend, and automated verification agents.

## ✨ Features

- **Monorepo Architecture**: Clean separation between `backend/`, `frontend/`, and `docs/`.
- **Agent Network**: Integrated AI agents for system monitoring, security audits, and automated fixes.
- **Design System**: Comprehensive `DESIGN.md` and `DOCS.md` for consistent development.
- **Verification Agents**: Automated verification of the entire infrastructure state.
- **Migration Logic**: Secure and documented migration paths for system updates.

## 🛠️ Tech Stack

- **Backend**: Python-based AI orchestration.
- **Frontend**: React-driven dashboard.
- **Infrastructure**: Pre-commit hooks and automated verification scripts.
- **Documentation**: Markdown-first with design and Design system.

## 🚀 Getting Started

```bash
# Set up pre-commit hooks
pre-commit install

# Check system warnings
python check_warning.py

# Run the backend
cd backend/ && python main.py
```

## 🛡️ Antigravity Protocol

This project follows the **Antigravity** code standards:
- **Modular Monorepo**: Strictly isolated backend and frontend logic.
- **150-Line Limit**: Applied to all management scripts and core logic.
- **Strict Verification**: Every change must pass the automated agent network check.
- **Security First**: All infrastructure decisions are documented in `DESIGN.md`.

---

*"Infrastructure is the spine of intelligence."*
