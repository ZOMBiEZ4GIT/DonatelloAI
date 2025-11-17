# 🛠️ Developer Setup Guide
## DonatelloAI Platform

> **Quick start guide for developers**

---

## Prerequisites

### Required Software

- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **Node.js 18+**: [Download](https://nodejs.org/)
- **Docker Desktop**: [Download](https://www.docker.com/products/docker-desktop)
- **Git**: [Download](https://git-scm.com/)
- **VSCode** (recommended): [Download](https://code.visualstudio.com/)

### Azure Resources (for full functionality)

- Azure subscription
- Azure AD tenant
- Azure SQL Database
- Azure Blob Storage
- Azure Key Vault
- Azure Cosmos DB

---

## Quick Start (Docker)

```bash
# 1. Clone repository
git clone https://github.com/your-org/DonatelloAI.git
cd DonatelloAI

# 2. Copy environment file
cp .env.example .env

# 3. Update .env with your credentials
# At minimum, set:
# - AZURE_TENANT_ID
# - AZURE_CLIENT_ID
# - AZURE_CLIENT_SECRET
# - DATABASE_URL
# - AZURE_STORAGE_CONNECTION_STRING

# 4. Start all services
docker-compose up -d

# 5. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Backend Setup (Manual)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v --cov=app --cov-report=html

# Run linting
black app/ tests/
ruff check app/ tests/
mypy app/
```

---

## Frontend Setup (Manual)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run linting
npm run lint
npm run type-check
```

---

## IDE Setup (VSCode)

### Recommended Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker",
    "ms-vscode.azurecli",
    "redhat.vscode-yaml"
  ]
}
```

### Settings

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.banditEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## Environment Variables

See `.env.example` for complete list. Key variables:

```bash
# App
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/donatelloai
COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key

# Azure AD
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# Model Providers
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...
ADOBE_API_KEY=your-adobe-key
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code
- Add tests (required, >80% coverage)
- Update documentation

### 3. Run Quality Checks

```bash
# Backend
pytest && black . && ruff check . && mypy .

# Frontend
npm test && npm run lint && npm run type-check
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
# Commit message format: type(scope): description
# Types: feat, fix, docs, style, refactor, test, chore
```

### 5. Push and Create PR

```bash
git push -u origin feature/your-feature-name
# Then create Pull Request on GitHub
```

---

## Debugging

### Backend Debugging (VSCode)

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Frontend Debugging

- Use browser DevTools (F12)
- React DevTools extension
- Enable source maps in Vite

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
**Solution**: Ensure virtual environment is activated and dependencies installed

**Issue**: Database connection error
**Solution**: Check `DATABASE_URL` in `.env`, ensure PostgreSQL is running

**Issue**: CORS errors in frontend
**Solution**: Verify `CORS_ORIGINS` in backend `.env` includes `http://localhost:5173`

**Issue**: Docker containers not starting
**Solution**: Run `docker-compose down && docker-compose up --build`

---

## Resources

- [Full Documentation](docs/)
- [API Reference](docs/api/openapi.yaml)
- [Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

---

## Support

- **Slack**: #donatelloai-dev
- **Email**: dev-support@donatelloai.com.au
- **Issues**: GitHub Issues
