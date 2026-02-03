# Contributing to Infrastructure Agent Manager

We welcome contributions! Please follow these guidelines.

## Development Setup

### Backend
1. Install `uv`: `pip install uv`
2. Sync dependencies: `cd backend && uv sync`
3. Run tests: `uv run pytest`

### Frontend
1. Install dependencies: `cd frontend && npm install`
2. Run lint: `npm run lint`

## Pull Request Process
1. Use the `PULL_REQUEST_TEMPLATE.md`.
2. Ensure all tests pass.
3. If adding a new feature, add a corresponding test.
4. Keep logic changes concise.

## Coding Standards
- **Python**: Follow PEP 8.
- **TypeScript**: No `any` types (unless explicitly disabled).
- **Commits**: Use Semantic Commit Messages (feat, fix, docs, chore).
