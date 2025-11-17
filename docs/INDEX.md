# 📚 DonatelloAI Documentation Index

> **Complete documentation navigation for the Enterprise Image Generation Platform**

---

## 🚀 Quick Start Guides

| Document | Audience | Purpose |
|----------|----------|---------|
| [README.md](../README.md) | All | Project overview and quick start |
| [DEVELOPER_SETUP.md](../DEVELOPER_SETUP.md) | Developers | Local development environment setup |
| [HUMAN_TASKS.md](../HUMAN_TASKS.md) | DevOps, Admins | Manual setup tasks and checkpoints |

---

## 🏗️ Architecture Documentation

### System Design

| Document | Description |
|----------|-------------|
| [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md) | Complete system architecture with all layers and components |
| [DATABASE_SCHEMA.md](architecture/DATABASE_SCHEMA.md) | Database design, ERD diagrams, and schema specifications |
| [AUTHENTICATION_ARCHITECTURE.md](architecture/AUTHENTICATION_ARCHITECTURE.md) | OAuth 2.0 flow, RBAC design, session management |
| [SECURITY_ARCHITECTURE.md](architecture/SECURITY_ARCHITECTURE.md) | Defense in depth, ISO 27001 controls, threat model |

### Diagrams

| Document | Description |
|----------|-------------|
| [DATA_FLOW_DIAGRAMS.md](diagrams/DATA_FLOW_DIAGRAMS.md) | Mermaid diagrams for all data flows (auth, generation, audit, etc.) |
| [Architecture Diagrams](architecture/SYSTEM_ARCHITECTURE.md#high-level-architecture) | System context, logical, and physical architecture |

---

## 📡 API Documentation

| Document | Description |
|----------|-------------|
| [openapi.yaml](api/openapi.yaml) | Complete OpenAPI 3.0 specification for all endpoints |
| [API Reference Online](#) | Interactive API documentation (Swagger UI) |
| [Postman Collection](#) | Ready-to-use Postman collection for testing |

**API Sections**:
- Health & Status Endpoints
- Authentication & Authorization
- Image Generation
- User Management (Admin)
- Department & Budget Management
- Audit Logs & Compliance
- Webhooks

---

## 💼 Business Documentation

| Document | Audience | Description |
|----------|----------|-------------|
| [EXECUTIVE_SUMMARY.md](business/EXECUTIVE_SUMMARY.md) | Executives, Investors | Business case, market analysis, financial projections |
| [enterprise-imagen-spec.md](../enterprise-imagen-spec.md) | All stakeholders | Original product specification and requirements |
| [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) | Developers | Detailed codebase organization and design principles |

---

## 🔒 Security & Compliance

| Document | Purpose |
|----------|---------|
| [SECURITY_ARCHITECTURE.md](architecture/SECURITY_ARCHITECTURE.md) | Security controls, threat model, incident response |
| [ISO 27001 Compliance](compliance/iso27001-mapping.md) | Control implementation mapping |
| [Privacy Impact Assessment](compliance/privacy-impact.md) | PIA for Privacy Act compliance |
| [Security Policy](../SECURITY.md) | Vulnerability disclosure, security contact |

---

## 🚀 Deployment & Operations

### Infrastructure

| Document | Description |
|----------|-------------|
| [Terraform Configurations](../infrastructure/terraform/) | Infrastructure as Code for all environments |
| [Kubernetes Manifests](../infrastructure/kubernetes/) | AKS deployment configurations |
| [Docker Compose](../docker-compose.yml) | Local development stack |

### Runbooks

| Document | Purpose |
|----------|---------|
| [Deployment Guide](runbooks/deployment.md) | Step-by-step deployment procedures |
| [Incident Response](runbooks/incident-response.md) | IR playbooks for security incidents |
| [Backup & Restore](runbooks/backup-restore.md) | Data recovery procedures |
| [Scaling Guide](runbooks/scaling.md) | Horizontal and vertical scaling |

---

## 🧪 Testing & Quality

| Document | Description |
|----------|-------------|
| [Testing Strategy](testing/strategy.md) | Unit, integration, E2E testing approach |
| [Test Coverage Report](../backend/htmlcov/index.html) | Backend code coverage (generated) |
| [Playwright E2E Tests](../frontend/tests/e2e/) | End-to-end test suites |

---

## 📋 Development Guidelines

| Document | Purpose |
|----------|---------|
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines and code review process |
| [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Community standards and behavior expectations |
| [Git Workflow](development/git-workflow.md) | Branch strategy, commit conventions |
| [Code Style Guide](development/code-style.md) | Python and TypeScript style standards |

---

## 📊 Project Management

| Document | Description |
|----------|-------------|
| [HUMAN_TASKS.md](../HUMAN_TASKS.md) | Critical checkpoints requiring human decisions |
| [Roadmap](roadmap/product-roadmap.md) | Feature development timeline |
| [Sprint Planning](project/sprint-planning.md) | Agile sprint process |
| [Release Notes](releases/) | Version history and changelog |

---

## 📖 Reference Documentation

### Technology Stack

| Component | Documentation |
|-----------|---------------|
| **Backend** | [FastAPI Docs](https://fastapi.tiangolo.com/) |
| **Frontend** | [React Docs](https://react.dev/), [Vite Docs](https://vitejs.dev/) |
| **Database** | [Azure SQL Docs](https://learn.microsoft.com/en-us/azure/azure-sql/) |
| **Cloud** | [Azure Docs](https://learn.microsoft.com/en-us/azure/) |

### External APIs

| Provider | Documentation |
|----------|---------------|
| Azure OpenAI | [Azure OpenAI Docs](https://learn.microsoft.com/en-us/azure/ai-services/openai/) |
| Replicate | [Replicate Docs](https://replicate.com/docs) |
| Adobe Firefly | [Adobe API Docs](https://developer.adobe.com/firefly-services/) |

---

## 🎯 Documentation by Role

### For Developers

1. [DEVELOPER_SETUP.md](../DEVELOPER_SETUP.md) - Get started
2. [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md) - Understand the system
3. [DATABASE_SCHEMA.md](architecture/DATABASE_SCHEMA.md) - Database design
4. [openapi.yaml](api/openapi.yaml) - API reference
5. [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines

### For DevOps/SRE

1. [HUMAN_TASKS.md](../HUMAN_TASKS.md) - Setup checklist
2. [Deployment Guide](runbooks/deployment.md) - Deployment procedures
3. [Infrastructure Code](../infrastructure/) - Terraform and Kubernetes
4. [Incident Response](runbooks/incident-response.md) - IR playbooks
5. [Monitoring Guide](runbooks/monitoring.md) - Observability setup

### For Security Team

1. [SECURITY_ARCHITECTURE.md](architecture/SECURITY_ARCHITECTURE.md) - Security design
2. [AUTHENTICATION_ARCHITECTURE.md](architecture/AUTHENTICATION_ARCHITECTURE.md) - Auth flows
3. [ISO 27001 Mapping](compliance/iso27001-mapping.md) - Compliance controls
4. [Incident Response](runbooks/incident-response.md) - Security incidents
5. [Vulnerability Management](security/vulnerability-mgmt.md) - Vuln process

### For Compliance/Auditors

1. [ISO 27001 Mapping](compliance/iso27001-mapping.md) - Control implementation
2. [Audit Log Viewer](admin/audit-logs.md) - 7-year audit trail
3. [Privacy Impact Assessment](compliance/privacy-impact.md) - Privacy compliance
4. [Data Flow Diagrams](diagrams/DATA_FLOW_DIAGRAMS.md) - Data processing
5. [Security Architecture](architecture/SECURITY_ARCHITECTURE.md) - Security controls

### For Product/Business

1. [EXECUTIVE_SUMMARY.md](business/EXECUTIVE_SUMMARY.md) - Business case
2. [enterprise-imagen-spec.md](../enterprise-imagen-spec.md) - Product specification
3. [Roadmap](roadmap/product-roadmap.md) - Feature timeline
4. [User Personas](business/user-personas.md) - Target users
5. [Competitive Analysis](business/competitive-analysis.md) - Market positioning

---

## 🔄 Documentation Maintenance

### Update Frequency

| Documentation Type | Update Trigger |
|-------------------|----------------|
| **API Docs** | Every API change (automated) |
| **Architecture** | Major design changes |
| **Database Schema** | Every migration |
| **Security** | Quarterly review + after incidents |
| **Business Docs** | Monthly or after major milestones |

### Documentation Standards

- All docs in Markdown format
- Mermaid for diagrams
- OpenAPI 3.0 for API specs
- ISO 8601 for dates
- Semantic versioning for releases

### Contributing to Docs

1. Follow [Markdown Style Guide](development/markdown-style.md)
2. Use Mermaid for all diagrams
3. Include table of contents for docs > 200 lines
4. Add examples and code snippets
5. Keep language clear and concise

---

## 📞 Support & Contact

| Type | Contact |
|------|---------|
| **Developer Questions** | #donatelloai-dev on Slack |
| **Security Issues** | security@donatelloai.com.au |
| **Documentation Bugs** | Create GitHub issue with `docs` label |
| **General Support** | support@donatelloai.com.au |

---

## 📄 Document Control

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Last Updated | 2025-11-17 |
| Maintained By | Documentation Team |
| Review Cycle | Monthly |

---

**Next Steps**:
- New to the project? Start with [DEVELOPER_SETUP.md](../DEVELOPER_SETUP.md)
- Need to understand the architecture? See [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md)
- Looking for API details? Check [openapi.yaml](api/openapi.yaml)
- Deploying to production? Follow [Deployment Guide](runbooks/deployment.md)
