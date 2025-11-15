# Enterprise Image Generation Platform - Project Structure

> **Purpose**: This document explains the enterprise-grade project structure and architectural decisions.
> **Audience**: Development team, security auditors, DevOps engineers
> **Last Updated**: 2025-11-15

---

## 🏗️ High-Level Architecture

```
DonatelloAI/
├── backend/                    # Python FastAPI backend service
├── frontend/                   # React TypeScript frontend
├── infrastructure/             # Infrastructure as Code (Terraform + K8s)
├── security/                   # Security policies and scanning configs
├── compliance/                 # ISO 27001 documentation and controls
├── docs/                       # Technical documentation
├── scripts/                    # Operational scripts
├── config/                     # Environment-specific configuration
└── .github/                    # CI/CD workflows
```

---

## 📁 Detailed Structure

### Backend Service (`/backend`)

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/           # API route handlers
│   │       │   ├── auth.py          # 🔐 Authentication endpoints
│   │       │   ├── generation.py    # 🎨 Image generation endpoints
│   │       │   ├── admin.py         # 👤 Admin management endpoints
│   │       │   ├── models.py        # 🤖 Model management endpoints
│   │       │   ├── departments.py   # 🏢 Department management
│   │       │   ├── users.py         # 👥 User management
│   │       │   ├── audit.py         # 📊 Audit log endpoints
│   │       │   └── health.py        # ❤️ Health check endpoints
│   │       └── dependencies/        # Route dependencies
│   │           ├── auth.py          # Auth dependency injection
│   │           ├── database.py      # DB session management
│   │           └── permissions.py   # RBAC permission checks
│   ├── core/
│   │   ├── config.py               # 🔧 Application configuration
│   │   ├── security.py             # 🔐 Security utilities (hashing, tokens)
│   │   ├── logging.py              # 📝 Structured logging setup
│   │   ├── exceptions.py           # ⚠️ Custom exception classes
│   │   └── middleware.py           # 🌐 Custom middleware (CORS, logging)
│   ├── models/
│   │   ├── user.py                 # 👤 User SQLAlchemy model
│   │   ├── department.py           # 🏢 Department model
│   │   ├── generation.py           # 🎨 Generation model
│   │   ├── audit_log.py            # 📊 Audit log model
│   │   ├── api_key.py              # 🔑 API key model
│   │   └── budget.py               # 💰 Budget tracking model
│   ├── schemas/
│   │   ├── user.py                 # 👤 User Pydantic schemas
│   │   ├── generation.py           # 🎨 Generation request/response schemas
│   │   ├── auth.py                 # 🔐 Auth schemas
│   │   └── common.py               # 📦 Shared schemas
│   ├── services/
│   │   ├── auth/
│   │   │   ├── azure_ad.py         # 🔐 Azure AD integration
│   │   │   ├── token_service.py    # 🎟️ JWT token management
│   │   │   └── rbac.py             # 🛡️ Role-based access control
│   │   ├── generation/
│   │   │   ├── model_router.py     # 🧠 Intelligent model selection
│   │   │   ├── prompt_processor.py # 📝 Prompt validation & enhancement
│   │   │   ├── pii_detector.py     # 🔍 PII detection service
│   │   │   ├── content_filter.py   # 🚫 NSFW content filtering
│   │   │   └── image_processor.py  # 🖼️ Post-processing & optimization
│   │   ├── models/
│   │   │   ├── base.py             # 🔌 Base model provider interface
│   │   │   ├── dalle.py            # 🎨 DALL-E 3 integration
│   │   │   ├── stable_diffusion.py # 🎨 Stable Diffusion integration
│   │   │   ├── adobe_firefly.py    # 🎨 Adobe Firefly integration
│   │   │   └── azure_ai.py         # 🎨 Azure AI Image integration
│   │   ├── storage/
│   │   │   ├── blob_storage.py     # 💾 Azure Blob Storage service
│   │   │   └── cdn.py              # 🌐 CDN integration
│   │   ├── cost/
│   │   │   ├── tracker.py          # 💰 Real-time cost tracking
│   │   │   ├── budget_enforcer.py  # 🚨 Budget limit enforcement
│   │   │   └── allocator.py        # 📊 Cost allocation service
│   │   ├── audit/
│   │   │   ├── logger.py           # 📝 Audit logging service
│   │   │   └── cosmos_db.py        # 🌐 Cosmos DB integration
│   │   └── monitoring/
│   │       ├── metrics.py          # 📊 Custom metrics collection
│   │       └── app_insights.py     # 📈 Application Insights integration
│   ├── utils/
│   │   ├── retry.py                # 🔄 Retry logic with exponential backoff
│   │   ├── encryption.py           # 🔐 Encryption utilities
│   │   ├── validators.py           # ✅ Custom validators
│   │   └── helpers.py              # 🛠️ Common helper functions
│   └── main.py                     # 🚀 FastAPI application entry point
├── tests/
│   ├── unit/                       # 🧪 Unit tests
│   │   ├── test_auth.py
│   │   ├── test_model_router.py
│   │   ├── test_pii_detector.py
│   │   └── test_cost_tracker.py
│   ├── integration/                # 🔗 Integration tests
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   └── test_model_providers.py
│   ├── e2e/                        # 🎭 End-to-end tests
│   │   └── test_generation_flow.py
│   ├── conftest.py                 # 🔧 Pytest configuration
│   └── fixtures/                   # 📦 Test fixtures
├── alembic/
│   ├── versions/                   # 📜 Database migrations
│   ├── env.py                      # 🌍 Alembic environment
│   └── alembic.ini                 # ⚙️ Alembic configuration
├── Dockerfile                      # 🐳 Production container
├── Dockerfile.dev                  # 🐳 Development container
├── requirements.txt                # 📦 Production dependencies
├── requirements-dev.txt            # 🔧 Development dependencies
└── pyproject.toml                  # 📋 Python project configuration
```

**Security Considerations (ISO 27001 A.12.1.1)**:
- All services implement retry logic with exponential backoff
- PII detection runs BEFORE external API calls
- All database queries use parameterized statements
- Secret rotation implemented via Azure Key Vault
- Rate limiting enforced at service layer

---

### Frontend Application (`/frontend`)

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginButton.tsx      # 🔐 Azure AD login integration
│   │   │   ├── ProtectedRoute.tsx   # 🛡️ Route protection wrapper
│   │   │   └── RoleGuard.tsx        # 👮 Role-based component rendering
│   │   ├── admin/
│   │   │   ├── Dashboard.tsx        # 📊 Admin dashboard
│   │   │   ├── UserManagement.tsx   # 👥 User CRUD
│   │   │   ├── DepartmentBudget.tsx # 💰 Budget management
│   │   │   ├── AuditLogViewer.tsx   # 📋 Audit log interface
│   │   │   └── ModelConfig.tsx      # ⚙️ Model configuration
│   │   ├── generation/
│   │   │   ├── PromptInput.tsx      # ✏️ Prompt input with validation
│   │   │   ├── ModelSelector.tsx    # 🤖 Manual model selection
│   │   │   ├── GenerationQueue.tsx  # 📋 User's generation history
│   │   │   ├── ImageViewer.tsx      # 🖼️ Image display & download
│   │   │   └── ProgressTracker.tsx  # 📊 WebSocket progress updates
│   │   └── common/
│   │       ├── Header.tsx           # 🎯 Navigation header
│   │       ├── Sidebar.tsx          # 📑 Sidebar navigation
│   │       ├── ErrorBoundary.tsx    # ⚠️ Error handling
│   │       └── LoadingSpinner.tsx   # ⏳ Loading states
│   ├── hooks/
│   │   ├── useAuth.ts              # 🔐 Authentication hook
│   │   ├── useWebSocket.ts         # 🔌 WebSocket connection hook
│   │   ├── useGeneration.ts        # 🎨 Generation state management
│   │   └── usePermissions.ts       # 🛡️ Permission checking hook
│   ├── services/
│   │   ├── api.ts                  # 🌐 Axios API client
│   │   ├── auth.ts                 # 🔐 Auth service
│   │   ├── generation.ts           # 🎨 Generation API calls
│   │   └── websocket.ts            # 🔌 WebSocket service
│   ├── utils/
│   │   ├── validators.ts           # ✅ Form validation
│   │   ├── formatters.ts           # 📝 Data formatting
│   │   └── constants.ts            # 📋 Application constants
│   ├── types/
│   │   ├── user.ts                 # 👤 User types
│   │   ├── generation.ts           # 🎨 Generation types
│   │   └── api.ts                  # 🌐 API response types
│   ├── pages/
│   │   ├── Home.tsx                # 🏠 Landing page
│   │   ├── Generate.tsx            # 🎨 Main generation interface
│   │   ├── Admin.tsx               # 👑 Admin panel
│   │   ├── Profile.tsx             # 👤 User profile
│   │   └── NotFound.tsx            # 404 page
│   ├── styles/
│   │   ├── globals.css             # 🎨 Global styles
│   │   └── tailwind.css            # 🎨 Tailwind imports
│   ├── App.tsx                     # 🚀 Root component
│   ├── index.tsx                   # 🚀 Application entry point
│   └── vite-env.d.ts               # 🔧 Vite type definitions
├── public/
│   ├── index.html                  # 📄 HTML template
│   └── assets/                     # 🖼️ Static assets
├── tests/
│   ├── unit/                       # 🧪 Component tests
│   ├── integration/                # 🔗 Integration tests
│   └── e2e/                        # 🎭 Playwright E2E tests
├── Dockerfile                      # 🐳 Production container
├── package.json                    # 📦 NPM dependencies
├── tsconfig.json                   # 🔧 TypeScript configuration
├── vite.config.ts                  # ⚡ Vite build configuration
├── tailwind.config.js              # 🎨 Tailwind CSS configuration
└── .eslintrc.js                    # 📏 ESLint rules
```

**Security Considerations (ISO 27001 A.14.2.1)**:
- All API calls include CSRF tokens
- Sensitive data never stored in localStorage (only httpOnly cookies)
- Content Security Policy (CSP) headers enforced
- Subresource Integrity (SRI) for external scripts
- Automatic token refresh before expiration

---

### Infrastructure as Code (`/infrastructure`)

```
infrastructure/
├── terraform/
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── main.tf             # 🌍 Dev environment orchestration
│   │   │   ├── variables.tf        # 📊 Dev-specific variables
│   │   │   └── terraform.tfvars    # 🔒 Dev values (gitignored)
│   │   ├── staging/
│   │   │   └── ...                 # 🎭 Staging environment
│   │   └── prod/
│   │       └── ...                 # 🚀 Production environment
│   └── modules/
│       ├── aks/
│       │   ├── main.tf             # ☸️ Azure Kubernetes Service
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── networking/
│       │   ├── vnet.tf             # 🌐 Virtual Network
│       │   ├── subnets.tf          # 📡 Subnets
│       │   ├── nsg.tf              # 🔒 Network Security Groups
│       │   └── front_door.tf       # 🚪 Azure Front Door + WAF
│       ├── storage/
│       │   ├── sql.tf              # 🗄️ Azure SQL Database
│       │   ├── cosmos.tf           # 🌐 Cosmos DB (audit logs)
│       │   ├── blob.tf             # 💾 Blob Storage (images)
│       │   └── key_vault.tf        # 🔐 Azure Key Vault
│       ├── security/
│       │   ├── entra_id.tf         # 👤 Azure Entra ID config
│       │   ├── rbac.tf             # 🛡️ Role assignments
│       │   ├── policies.tf         # 📋 Azure Policy
│       │   └── defender.tf         # 🛡️ Azure Defender
│       └── monitoring/
│           ├── app_insights.tf     # 📊 Application Insights
│           ├── log_analytics.tf    # 📝 Log Analytics Workspace
│           ├── alerts.tf           # 🚨 Alert rules
│           └── sentinel.tf         # 🔍 Azure Sentinel SIEM
├── kubernetes/
│   ├── base/
│   │   ├── namespace.yaml          # 📦 Namespace definition
│   │   ├── deployments/
│   │   │   ├── api-gateway.yaml    # 🌐 API Gateway deployment
│   │   │   ├── model-router.yaml   # 🧠 Model router service
│   │   │   └── worker.yaml         # 👷 Background workers
│   │   ├── services/
│   │   │   ├── api-gateway-svc.yaml
│   │   │   └── internal-svc.yaml
│   │   ├── configmaps/
│   │   │   └── app-config.yaml     # ⚙️ Application config
│   │   ├── secrets/
│   │   │   └── sealed-secrets.yaml # 🔐 Encrypted secrets
│   │   └── ingress/
│   │       └── ingress.yaml        # 🚪 Ingress controller
│   └── overlays/
│       ├── dev/                    # 🔧 Dev-specific overrides
│       ├── staging/                # 🎭 Staging overrides
│       └── prod/                   # 🚀 Production overrides
└── helm/
    └── eig-platform/               # ⎈ Helm chart (future)
```

**Infrastructure Security (ISO 27001 A.13.1.1)**:
- All resources deployed in Australia East/Southeast regions
- Private endpoints for storage accounts (no public internet access)
- Network segmentation with NSGs
- All secrets stored in Key Vault with managed identities
- Infrastructure drift detection via Terraform Cloud

---

### Security Framework (`/security`)

```
security/
├── policies/
│   ├── azure-policy/
│   │   ├── allowed-locations.json   # 🌏 Enforce Australia regions
│   │   ├── require-encryption.json  # 🔐 Mandatory encryption
│   │   └── deny-public-access.json  # 🚫 No public endpoints
│   ├── network-policies/
│   │   └── k8s-network-policy.yaml  # 🔒 Kubernetes network isolation
│   └── rbac/
│       ├── roles.yaml               # 👮 Custom RBAC roles
│       └── bindings.yaml            # 🔗 Role bindings
├── scanning/
│   ├── trivy-config.yaml           # 🔍 Container scanning
│   ├── sonarqube-config.xml        # 📊 SAST configuration
│   └── dependency-check.xml        # 📦 Dependency scanning
└── secrets/
    ├── .gitattributes              # 🔒 Prevent secret commits
    └── secret-patterns.txt         # 🔍 Secret detection patterns
```

---

### Compliance Documentation (`/compliance`)

```
compliance/
├── iso27001/
│   ├── controls/
│   │   ├── A.5-policies.md         # 📋 Information security policies
│   │   ├── A.8-asset-mgmt.md       # 🏷️ Asset management
│   │   ├── A.9-access-control.md   # 🔐 Access control
│   │   ├── A.12-operations.md      # ⚙️ Operations security
│   │   └── ...                     # (114 controls total)
│   ├── evidence/
│   │   ├── policy-approval/        # ✅ Approved policies
│   │   ├── audit-reports/          # 📊 Internal audit reports
│   │   └── training-records/       # 🎓 Security training logs
│   └── isms/
│       ├── scope.md                # 🎯 ISMS scope definition
│       ├── risk-register.xlsx      # ⚠️ Risk assessment
│       └── soa.md                  # 📋 Statement of Applicability
├── controls/
│   ├── technical-controls.md       # 🔧 Technical control mapping
│   ├── administrative-controls.md  # 📝 Administrative controls
│   └── physical-controls.md        # 🏢 Physical security controls
└── audit-templates/
    ├── access-review.xlsx          # 👥 Quarterly access reviews
    ├── incident-report.docx        # 🚨 Incident report template
    └── compliance-checklist.xlsx   # ✅ Audit checklist
```

**Compliance Notes**:
- All controls mapped to actual technical implementations
- Evidence collected automatically where possible
- Quarterly reviews scheduled via Azure Logic Apps
- Immutable audit logs retained for 7 years

---

### Operational Scripts (`/scripts`)

```
scripts/
├── deployment/
│   ├── deploy-dev.sh               # 🚀 Deploy to dev environment
│   ├── deploy-prod.sh              # 🚀 Production deployment
│   ├── rollback.sh                 # ⏪ Emergency rollback
│   └── smoke-test.sh               # 🧪 Post-deployment validation
├── monitoring/
│   ├── health-check.sh             # ❤️ Manual health verification
│   ├── cost-report.sh              # 💰 Generate cost reports
│   └── audit-export.sh             # 📊 Export audit logs
└── backup/
    ├── backup-database.sh          # 💾 Database backup
    └── restore-database.sh         # 🔄 Database restore
```

---

### Documentation (`/docs`)

```
docs/
├── architecture/
│   ├── adr/                        # 📝 Architecture Decision Records
│   │   ├── 001-azure-only.md
│   │   ├── 002-multi-model.md
│   │   └── 003-cosmos-audit.md
│   ├── diagrams/                   # 📊 Architecture diagrams
│   │   ├── system-context.puml
│   │   ├── container-diagram.puml
│   │   └── deployment-view.puml
│   └── security-architecture.md    # 🔐 Security design
├── api/
│   ├── openapi.yaml                # 📖 OpenAPI specification
│   ├── postman-collection.json     # 📮 Postman collection
│   └── examples/                   # 📋 API usage examples
├── compliance/
│   ├── iso27001-mapping.md         # 🗺️ Control implementation mapping
│   ├── privacy-impact.md           # 🔒 Privacy impact assessment
│   └── data-flow-diagrams.md       # 🌊 Data flow documentation
├── runbooks/
│   ├── incident-response.md        # 🚨 Incident procedures
│   ├── deployment.md               # 🚀 Deployment procedures
│   ├── backup-restore.md           # 💾 Backup procedures
│   └── scaling.md                  # 📈 Scaling procedures
└── security/
    ├── threat-model.md             # ⚠️ Threat modeling
    ├── pentest-results/            # 🔍 Penetration test reports
    └── vulnerability-mgmt.md       # 🐛 Vulnerability management
```

---

## 🔧 Configuration Management

```
config/
├── dev/
│   ├── api.env                     # 🔧 API environment variables
│   ├── database.env                # 🗄️ Database connection strings
│   └── secrets.env.example         # 🔐 Secret template (not actual secrets)
├── staging/
│   └── ...                         # 🎭 Staging configuration
└── prod/
    └── ...                         # 🚀 Production configuration
```

**Configuration Security (ISO 27001 A.12.4.1)**:
- Actual secrets NEVER committed to Git
- All config files use environment variable substitution
- Secrets loaded from Azure Key Vault at runtime
- Separate Key Vaults per environment
- Configuration changes logged in audit trail

---

## 🐳 Docker Configuration

```
.
├── docker-compose.yml              # 🐳 Local development stack
├── docker-compose.prod.yml         # 🐳 Production stack (for testing)
└── .dockerignore                   # 🚫 Docker build exclusions
```

---

## 🔄 CI/CD Pipelines

```
.github/
└── workflows/
    ├── backend-ci.yml              # 🧪 Backend tests & linting
    ├── frontend-ci.yml             # 🧪 Frontend tests & linting
    ├── security-scan.yml           # 🔍 Security scanning
    ├── deploy-dev.yml              # 🚀 Deploy to dev
    ├── deploy-staging.yml          # 🚀 Deploy to staging
    ├── deploy-prod.yml             # 🚀 Deploy to production (manual)
    └── compliance-check.yml        # ✅ Compliance validation
```

**Pipeline Security (ISO 27001 A.12.1.2)**:
- All deployments require code review approval
- Production deployments require manual approval
- Security scans must pass before merge
- Secrets managed via GitHub Secrets + Azure Key Vault
- Deployment audit trail maintained

---

## 📦 Root-Level Files

```
.
├── .gitignore                      # 🚫 Git exclusions
├── .gitattributes                  # 🔒 Git attributes (secret prevention)
├── .editorconfig                   # 📝 Editor configuration
├── .env.example                    # 🔧 Environment template
├── README.md                       # 📖 Project overview
├── PROJECT_STRUCTURE.md            # 📁 This file
├── HUMAN_TASKS.md                  # ✅ Human task tracking
├── enterprise-imagen-spec.md       # 📋 Original specification
├── CONTRIBUTING.md                 # 🤝 Contribution guidelines
├── LICENSE                         # ⚖️ License
└── SECURITY.md                     # 🔒 Security policy
```

---

## 🎯 Design Principles Applied

### 1. Separation of Concerns
- **Backend**: Business logic isolated from infrastructure
- **Frontend**: Presentation separated from state management
- **Infrastructure**: Environment-agnostic modules

### 2. Security by Design (ISO 27001 A.14.1.1)
- No secrets in code or config files
- All external inputs validated
- Defense in depth across all layers
- Principle of least privilege enforced

### 3. Compliance-First Architecture
- Every component maps to ISO 27001 controls
- Audit trails built into all operations
- Evidence collection automated
- Traceability from requirement to implementation

### 4. Cloud-Native Design
- 12-factor app principles
- Stateless services
- Configuration via environment
- Horizontal scaling support
- Health checks and graceful shutdown

### 5. Developer Experience
- Clear naming conventions
- Comprehensive documentation
- Local development mirrors production
- Fast feedback loops (CI/CD)
- Type safety (TypeScript + Python type hints)

---

## 🚀 Getting Started

### Prerequisites
See `HUMAN_TASKS.md` for complete setup requirements.

### Local Development
```bash
# Clone repository
git clone <repo-url>
cd DonatelloAI

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend
npm run test
npm run test:e2e
```

---

## 📞 Support and Questions

- **Technical Issues**: Create issue in repository
- **Security Concerns**: See SECURITY.md for responsible disclosure
- **Compliance Questions**: Contact compliance@[org].com.au
- **Emergency**: Follow runbooks in `docs/runbooks/`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Owner**: Platform Architecture Team
**Review Cycle**: Monthly
