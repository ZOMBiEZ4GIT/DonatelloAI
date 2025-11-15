# 🎨 Enterprise Image Generation Platform

> **Mission-Critical**: ISO 27001-compliant, multi-model AI image generation platform for Australian enterprises

[![Security](https://img.shields.io/badge/security-ISO%2027001-blue)](docs/compliance)
[![Azure](https://img.shields.io/badge/cloud-Azure-0078D4)](infrastructure/)
[![Python](https://img.shields.io/badge/python-3.11-3776AB)](backend/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0-3178C6)](frontend/)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

---

## 🎯 What Is This?

An **enterprise-grade platform** that aggregates multiple AI image generation models (DALL-E 3, Stable Diffusion XL, Adobe Firefly, Azure AI) through a unified, secure interface with:

- ✅ **ISO 27001 & ISO/IEC 23053 compliance**
- 🇦🇺 **Australian data sovereignty** (Azure Australia regions)
- 💰 **Cost management** (department budgets, intelligent routing)
- 🔐 **Enterprise authentication** (Azure Entra ID + MFA)
- 📊 **Comprehensive audit trails** (7-year retention)
- 🚀 **99.95% uptime SLA**

---

## 🏗️ Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│              Azure Front Door + WAF                      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│           Azure Kubernetes Service (AKS)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ FastAPI  │  │  Model   │  │  Auth    │              │
│  │ Gateway  │  │  Router  │  │ Service  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Azure SQL │ Cosmos DB │ Blob Storage │ Key Vault      │
│ (Metadata) │  (Audit)  │   (Images)   │  (Secrets)     │
└─────────────────────────────────────────────────────────┘
```

**Full architecture**: See [docs/architecture/](docs/architecture/)

---

## 🚀 Quick Start

### Prerequisites

**Critical**: Before running this project, complete tasks in [`HUMAN_TASKS.md`](HUMAN_TASKS.md):
- Azure subscription with billing account
- Azure AD tenant configured
- Azure Key Vault created
- Model provider API keys obtained

### Local Development Setup

```bash
# 1. Clone and navigate
git clone <repository-url>
cd DonatelloAI

# 2. Copy environment template
cp .env.example .env
# Edit .env with your Azure credentials

# 3. Start backend (Python 3.11 required)
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# 4. Start frontend (Node 18+ required)
cd ../frontend
npm install
npm run dev  # Runs on http://localhost:5173

# 5. Access application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Docker Development (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📂 Project Structure

```
DonatelloAI/
├── backend/              # FastAPI Python backend
├── frontend/             # React TypeScript frontend
├── infrastructure/       # Terraform + Kubernetes IaC
├── security/             # Security policies & scanning
├── compliance/           # ISO 27001 documentation
├── docs/                 # Technical documentation
└── scripts/              # Operational scripts
```

**Detailed structure**: See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## 🔐 Security First

This platform handles **sensitive corporate data** and is designed for **external security audits**.

### Security Principles
1. ✅ **Zero Trust**: All requests authenticated and authorized
2. ✅ **Encryption Everywhere**: TLS 1.3 in transit, AES-256 at rest
3. ✅ **Least Privilege**: RBAC with 5 granular roles
4. ✅ **Audit Everything**: Immutable logs for 7 years
5. ✅ **Defense in Depth**: Multiple security layers

### Reporting Security Issues
**DO NOT** open public issues for security vulnerabilities.
See [SECURITY.md](SECURITY.md) for responsible disclosure process.

---

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Unit tests with coverage
pytest tests/unit -v --cov=app --cov-report=html

# Integration tests (requires Azure credentials)
pytest tests/integration -v

# All tests
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Frontend Tests
```bash
cd frontend

# Unit tests
npm run test

# E2E tests with Playwright
npm run test:e2e

# Coverage report
npm run test:coverage
```

### Security Scans
```bash
# Container vulnerability scanning
trivy image <image-name>:latest

# Dependency scanning
safety check -r backend/requirements.txt

# SAST scanning
sonar-scanner
```

---

## 🚀 Deployment

### Development Environment
```bash
cd infrastructure/terraform/environments/dev
terraform init
terraform plan
terraform apply

# Deploy application
cd ../../../../scripts/deployment
./deploy-dev.sh
```

### Production Deployment

**⚠️ WARNING**: Production deployments require:
- [ ] Security audit completion
- [ ] Compliance review approval
- [ ] Change management ticket
- [ ] Stakeholder sign-off

```bash
# Production deployment (manual approval required)
cd scripts/deployment
./deploy-prod.sh

# Post-deployment validation
./smoke-test.sh production
```

**Runbooks**: See [docs/runbooks/deployment.md](docs/runbooks/deployment.md)

---

## 📊 Monitoring & Operations

### Health Checks
- **Application**: `https://<domain>/api/v1/health`
- **Azure Monitor**: Azure Portal > Monitor
- **Application Insights**: Real-time telemetry

### Dashboards
- **Admin Dashboard**: `https://<domain>/admin`
- **Cost Tracking**: `https://<domain>/admin/costs`
- **Audit Logs**: `https://<domain>/admin/audit`

### Incident Response
In case of incidents, see [docs/runbooks/incident-response.md](docs/runbooks/incident-response.md)

**On-Call**: incidents@[organization].com.au

---

## 📖 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Codebase organization | Developers |
| [HUMAN_TASKS.md](HUMAN_TASKS.md) | Manual setup tasks | DevOps, Admins |
| [docs/api/openapi.yaml](docs/api/openapi.yaml) | API specification | API consumers |
| [docs/architecture/](docs/architecture/) | System design | Architects, Auditors |
| [docs/compliance/](docs/compliance/) | ISO 27001 controls | Compliance team |
| [docs/runbooks/](docs/runbooks/) | Operational procedures | On-call engineers |

---

## 🤝 Contributing

This is an **enterprise project** with strict quality standards:

1. **Security**: All code must pass security scans
2. **Testing**: 100% test coverage for critical paths
3. **Documentation**: All functions documented with security notes
4. **Compliance**: Changes must maintain ISO 27001 compliance

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📋 Compliance & Certifications

### Current Status
- 🟡 **ISO 27001**: In progress (target: Month 12)
- 🟡 **ISO/IEC 23053** (AI): In progress
- ✅ **Privacy Act 1988** (Australia): Compliant
- ✅ **GDPR**: Data portability implemented
- ✅ **Azure Well-Architected Framework**: Followed

### Audit Trail
All platform activities are logged with:
- User identity (Azure AD ID)
- Action performed
- Timestamp (UTC)
- IP address and user agent
- Resource affected
- Operation result

**Audit retention**: 7 years (immutable storage)

---

## 💰 Cost Management

### Budget Controls
- **Department Budgets**: Hard limits enforced
- **Cost Tracking**: Real-time per image
- **Intelligent Routing**: Optimizes for cost vs quality
- **Usage Alerts**: Notify at 80%, 90%, 100% thresholds

### Cost Optimization
| Model | Cost/Image | Use Case |
|-------|-----------|----------|
| Stable Diffusion XL | $0.02 AUD | High volume, basic |
| Azure AI Image | $0.05 AUD | Balanced |
| DALL-E 3 | $0.08 AUD | High quality |
| Adobe Firefly | $0.10 AUD | Commercial safe |

**Target**: Average cost <$0.05 AUD per image

---

## 🎯 Success Metrics

### Technical KPIs (Current → Target)
- ⏱️ **API Latency P95**: - → <200ms
- ⬆️ **Uptime**: - → 99.95%
- ✅ **Generation Success**: - → >95%
- ⚡ **Avg Generation Time**: - → <15s

### Business KPIs
- 🏢 **Enterprise Customers**: 0 → 10 (Year 1)
- 💵 **ARR**: $0 → $2.5M (Year 2)
- 😊 **NPS Score**: - → >50
- 📉 **Cost per Image**: - → <$0.05 AUD

---

## 🌏 Regional Compliance

### Australian Data Sovereignty
- ✅ All data stored in **Azure Australia East/Southeast**
- ✅ No cross-border data transfers (except approved model APIs)
- ✅ Data residency guarantees contractually enforced
- ✅ APRA CPS 234 compliant (financial services)

### Supported Model Providers
| Provider | Data Region | Compliance Status |
|----------|-------------|-------------------|
| Azure OpenAI | Australia East | ✅ Compliant |
| Replicate | US (with DPA) | ⚠️ Requires data processing agreement |
| Adobe Firefly | Global | ⚠️ Enterprise contract required |
| Azure AI | Australia East | ✅ Compliant |

---

## 📞 Support

### For Users
- 📧 Email: support@[organization].com.au
- 📱 Phone: 1800-XXX-XXX (Business hours AEST)
- 🎫 Portal: https://support.[organization].com.au

### For Developers
- 💬 Slack: #eig-platform-dev
- 📖 Wiki: Confluence space
- 🐛 Issues: GitHub Issues

### Emergency Contacts
- 🚨 **Security Incident**: security@[organization].com.au
- 🔥 **Production Outage**: oncall@[organization].com.au
- 📊 **Compliance Concern**: compliance@[organization].com.au

---

## 📜 License

**Proprietary and Confidential**

Copyright © 2024 [Organization Name]. All rights reserved.

This software is proprietary. Unauthorized copying, distribution, or use is strictly prohibited.

See [LICENSE](LICENSE) for full terms.

---

## 🙏 Acknowledgments

- **Azure Architecture Team**: For infrastructure guidance
- **Security Review Board**: For threat modeling
- **Compliance Team**: For ISO 27001 framework
- **Model Providers**: OpenAI, Replicate, Adobe, Microsoft

---

**Project Status**: 🟡 In Active Development
**Last Updated**: 2025-11-15
**Next Milestone**: Checkpoint 1 - Authentication Architecture
