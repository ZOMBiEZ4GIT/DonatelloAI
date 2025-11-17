# 🏗️ System Architecture Design
## Enterprise Image Generation Platform (DonatelloAI)

> **Version**: 1.0
> **Date**: 2025-11-17
> **Status**: Design Phase
> **Classification**: CONFIDENTIAL

---

## Table of Contents

1. [Executive Overview](#executive-overview)
2. [System Context](#system-context)
3. [Architectural Principles](#architectural-principles)
4. [High-Level Architecture](#high-level-architecture)
5. [Component Architecture](#component-architecture)
6. [Data Architecture](#data-architecture)
7. [Integration Architecture](#integration-architecture)
8. [Security Architecture](#security-architecture)
9. [Deployment Architecture](#deployment-architecture)
10. [Scalability & Performance](#scalability--performance)
11. [Disaster Recovery](#disaster-recovery)
12. [Monitoring & Observability](#monitoring--observability)

---

## Executive Overview

### Purpose

The Enterprise Image Generation Platform (DonatelloAI) is a **mission-critical, ISO 27001-compliant system** designed to provide Australian enterprises with secure, governed, and cost-effective access to multiple AI image generation models through a unified interface.

### Key Architectural Drivers

| Driver | Requirement | Architectural Response |
|--------|-------------|----------------------|
| **Security** | ISO 27001 + ISO/IEC 23053 compliance | Defense-in-depth, zero-trust, comprehensive audit logging |
| **Data Sovereignty** | Australian data residency | Azure Australia East/Southeast regions only |
| **Availability** | 99.95% uptime SLA | Multi-region deployment, health monitoring, auto-scaling |
| **Cost Optimization** | <$0.05 AUD average per image | Intelligent model routing, department budgets, usage tracking |
| **Scalability** | 1M images/day, 10K concurrent users | Microservices on AKS, event-driven architecture, CDN |
| **Compliance** | 7-year immutable audit trail | Cosmos DB append-only logs, encryption at rest |

### Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND TIER                            │
│  React 18 + TypeScript + Tailwind CSS + Vite               │
│  MSAL React (Azure AD) + Zustand + React Query              │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     API GATEWAY TIER                         │
│  Azure Front Door + WAF + API Management                    │
│  Rate Limiting + Geo-Filtering + DDoS Protection            │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION TIER                           │
│  FastAPI (Python 3.11) + Uvicorn                            │
│  Celery + Redis + SQLAlchemy + Pydantic                     │
│  Presidio (PII) + Azure SDK                                 │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     DATA TIER                                │
│  Azure SQL (metadata) + Cosmos DB (audit)                   │
│  Blob Storage (images) + Key Vault (secrets)                │
│  Redis Cache (sessions) + Application Insights              │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                           │
│  Azure OpenAI (DALL-E 3) + Replicate (SD XL)               │
│  Adobe Firefly + Azure AI Image Generation                  │
└─────────────────────────────────────────────────────────────┘
```

---

## System Context

### System Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE ORGANIZATION                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Super Admin  │  │  Dept Manager│  │ Standard User│          │
│  │              │  │              │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┴─────────────────┘                   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │ HTTPS/TLS 1.3
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                  DONATELLOAI PLATFORM                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   TRUST BOUNDARY                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │ Web Frontend │  │  API Gateway │  │  Auth Service│     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │Model Router  │  │ Cost Tracker │  │ Audit Logger │     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │  Database    │  │Blob Storage  │  │  Key Vault   │     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────┬─────────────────────────────────────────────┘
                     │ HTTPS/API Keys
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXTERNAL AI PROVIDERS                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │Azure OpenAI  │  │  Replicate   │  │Adobe Firefly │           │
│  │  (DALL-E 3)  │  │   (SD XL)    │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────────────┘
```

### External Actors

| Actor | Role | Authentication | Authorization |
|-------|------|----------------|---------------|
| **Super Admin** | Platform configuration, all organizations | Azure AD + MFA | Full access |
| **Org Admin** | Organization-wide settings, compliance | Azure AD + MFA | Organization scope |
| **Dept Manager** | Budget management, user provisioning | Azure AD + MFA | Department scope |
| **Power User** | Unlimited generation, API access | Azure AD + MFA | Enhanced features |
| **Standard User** | Rate-limited generation | Azure AD + MFA | Basic features |
| **Azure AD** | Identity provider | N/A | Issues tokens |
| **AI Providers** | Image generation services | API keys | Rate limits apply |

---

## Architectural Principles

### 1. Security by Design

- **Zero Trust**: Every request authenticated and authorized
- **Defense in Depth**: Multiple security layers (WAF, network, application, data)
- **Least Privilege**: RBAC with granular permissions
- **Audit Everything**: Immutable logs for all operations
- **Encrypt Everything**: TLS 1.3 in transit, AES-256 at rest

### 2. Cloud-Native Architecture

- **Containerization**: All services run in Docker containers
- **Orchestration**: Kubernetes (AKS) for container management
- **Serverless Where Appropriate**: Azure Functions for event processing
- **Managed Services**: Leverage Azure PaaS to reduce operational overhead
- **Infrastructure as Code**: Terraform for reproducible deployments

### 3. Microservices Principles

- **Single Responsibility**: Each service has one clear purpose
- **Independent Deployment**: Services can be deployed independently
- **Technology Agnostic**: Right tool for the right job
- **Fault Isolation**: Failure in one service doesn't cascade
- **Observable**: Comprehensive logging, metrics, and tracing

### 4. API-First Design

- **RESTful APIs**: Standard HTTP verbs and status codes
- **OpenAPI Specification**: Machine-readable API contracts
- **Versioning**: Support multiple API versions concurrently
- **Rate Limiting**: Protect against abuse
- **Documentation**: Auto-generated from OpenAPI specs

### 5. Data Integrity & Compliance

- **Immutable Audit Logs**: Append-only Cosmos DB
- **Data Residency**: All data in Australia regions
- **PII Protection**: Presidio-based detection and redaction
- **Retention Policies**: Automated lifecycle management
- **Backup & Recovery**: Point-in-time restore capabilities

### 6. Performance & Scalability

- **Horizontal Scaling**: Add more pods/nodes under load
- **Caching Strategy**: Redis for sessions, CDN for images
- **Async Processing**: Celery for long-running tasks
- **Event-Driven**: Azure Service Bus for decoupling
- **CDN Distribution**: Azure Front Door for global reach

---

## High-Level Architecture

### Logical Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                          │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │  Web Application │  │  Mobile App      │                      │
│  │  (React SPA)     │  │  (Future)        │                      │
│  └──────────────────┘  └──────────────────┘                      │
└────────────────────────────┬──────────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────┴──────────────────────────────────────┐
│                           EDGE LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Azure Front Door (Global Load Balancer + CDN)          │    │
│  │  • WAF (Web Application Firewall)                        │    │
│  │  • DDoS Protection                                       │    │
│  │  • SSL/TLS Termination                                   │    │
│  │  • Geo-filtering (Australia focus)                       │    │
│  └──────────────────────────────────────────────────────────┘    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────┴──────────────────────────────────────┐
│                         API GATEWAY LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Azure API Management                                    │    │
│  │  • API Versioning                                        │    │
│  │  • Rate Limiting (tier-based)                            │    │
│  │  • Request/Response Transformation                       │    │
│  │  • API Analytics                                         │    │
│  └──────────────────────────────────────────────────────────┘    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────┴──────────────────────────────────────┐
│                      APPLICATION LAYER (AKS)                       │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  API Gateway      │  │  Authentication   │                    │
│  │  Service          │  │  Service          │                    │
│  │  (FastAPI)        │  │  (MSAL + JWT)     │                    │
│  └───────────────────┘  └───────────────────┘                    │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Model Router     │  │  Cost Management  │                    │
│  │  Service          │  │  Service          │                    │
│  │  (Selection AI)   │  │  (Budget Tracker) │                    │
│  └───────────────────┘  └───────────────────┘                    │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Generation       │  │  PII Detection    │                    │
│  │  Service          │  │  Service          │                    │
│  │  (Orchestration)  │  │  (Presidio)       │                    │
│  └───────────────────┘  └───────────────────┘                    │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Audit Logger     │  │  User Management  │                    │
│  │  Service          │  │  Service          │                    │
│  │  (Cosmos DB)      │  │  (RBAC)           │                    │
│  └───────────────────┘  └───────────────────┘                    │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Background Jobs  │  │  Notification     │                    │
│  │  (Celery Workers) │  │  Service          │                    │
│  │                   │  │  (Email/Webhook)  │                    │
│  └───────────────────┘  └───────────────────┘                    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────┴──────────────────────────────────────┐
│                         DATA LAYER                                 │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Azure SQL        │  │  Cosmos DB        │                    │
│  │  (Relational)     │  │  (Audit Logs)     │                    │
│  │  • Users          │  │  • Immutable logs │                    │
│  │  • Departments    │  │  • 7-year retention│                   │
│  │  • Generations    │  │  • Append-only    │                    │
│  └───────────────────┘  └───────────────────┘                    │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Blob Storage     │  │  Redis Cache      │                    │
│  │  (Images + CDN)   │  │  (Sessions)       │                    │
│  │  • Hot/Cool/Archive│  │  • Distributed   │                    │
│  │  • Lifecycle mgmt │  │  • Pub/Sub        │                    │
│  └───────────────────┘  └───────────────────┘                    │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Key Vault        │  │  Application      │                    │
│  │  (Secrets)        │  │  Insights         │                    │
│  │  • API keys       │  │  (Telemetry)      │                    │
│  │  • Certificates   │  │  • Metrics        │                    │
│  └───────────────────┘  └───────────────────┘                    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────┴──────────────────────────────────────┐
│                      INTEGRATION LAYER                             │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Azure OpenAI     │  │  Replicate API    │                    │
│  │  (DALL-E 3)       │  │  (SD XL)          │                    │
│  └───────────────────┘  └───────────────────┘                    │
│                                                                    │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  Adobe Firefly    │  │  Azure AI Image   │                    │
│  │  (Enterprise)     │  │  (Cognitive)      │                    │
│  └───────────────────┘  └───────────────────┘                    │
└────────────────────────────────────────────────────────────────────┘
```

### Physical Architecture (Azure Regions)

```
┌─────────────────────────────────────────────────────────────┐
│                    GLOBAL TIER                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Azure Front Door (Microsoft Global Network)       │     │
│  │  • Anycast IP                                      │     │
│  │  • WAF Rules (OWASP Top 10)                        │     │
│  │  • DDoS Protection Standard                        │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
         ▼                                     ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│  AUSTRALIA EAST (PRIMARY)│      │ AUSTRALIA SOUTHEAST     │
│  Sydney Region           │      │ Melbourne Region (DR)   │
├─────────────────────────┤      ├─────────────────────────┤
│                          │      │                         │
│ ┌─────────────────────┐ │      │ ┌─────────────────────┐│
│ │  AKS Cluster        │ │      │ │  AKS Cluster        ││
│ │  • 3 Node Pools     │ │      │ │  • 3 Node Pools     ││
│ │  • Auto-scaling     │ │      │ │  • Auto-scaling     ││
│ └─────────────────────┘ │      │ └─────────────────────┘│
│                          │      │                         │
│ ┌─────────────────────┐ │      │ ┌─────────────────────┐│
│ │  Azure SQL          │ │◄─────┼─┤  Azure SQL          ││
│ │  • Premium Tier     │ │ Geo  │ │  • Geo-replica      ││
│ │  • Active-Active    │ │Repli-│ │  • Read-only        ││
│ └─────────────────────┘ │cation│ └─────────────────────┘│
│                          │      │                         │
│ ┌─────────────────────┐ │      │ ┌─────────────────────┐│
│ │  Cosmos DB          │ │◄─────┼─┤  Cosmos DB          ││
│ │  • Multi-region     │ │ Auto │ │  • Automatic        ││
│ │  • Write region     │ │ Sync │ │  • Read region      ││
│ └─────────────────────┘ │      │ └─────────────────────┘│
│                          │      │                         │
│ ┌─────────────────────┐ │      │ ┌─────────────────────┐│
│ │  Blob Storage (GRS) │ │◄─────┼─┤  Blob Storage       ││
│ │  • Primary storage  │ │ Geo  │ │  • Secondary copy   ││
│ │  • CDN enabled      │ │Repli-│ │  • Read-only        ││
│ └─────────────────────┘ │cation│ └─────────────────────┘│
│                          │      │                         │
│ ┌─────────────────────┐ │      │ ┌─────────────────────┐│
│ │  Key Vault          │ │      │ │  Key Vault          ││
│ │  • Premium SKU      │ │      │ │  • Premium SKU      ││
│ │  • HSM-backed       │ │      │ │  • Replicated       ││
│ └─────────────────────┘ │      │ └─────────────────────┘│
└─────────────────────────┘      └─────────────────────────┘
```

---

## Component Architecture

### 1. API Gateway Service

**Purpose**: Main entry point for all API requests

**Responsibilities**:
- Request routing
- Authentication validation (JWT)
- Rate limiting enforcement
- Request/response logging
- CORS handling
- API versioning

**Technology**: FastAPI (Python 3.11)

**Endpoints**:
```
/api/v1/health/*          # Health checks
/api/v1/auth/*            # Authentication endpoints
/api/v1/generate          # Image generation
/api/v1/generations       # History & status
/api/v1/models            # Model information
/api/v1/admin/*           # Admin operations
/api/v1/users/*           # User management
```

**Configuration**:
- Max request size: 10 MB
- Request timeout: 60 seconds
- Workers: 4 per pod (CPU-bound)
- Auto-scaling: 3-20 pods

### 2. Authentication Service

**Purpose**: User authentication and authorization

**Responsibilities**:
- Azure AD integration (OAuth 2.0 + OIDC)
- JWT token validation and refresh
- Session management
- RBAC permission checks
- MFA enforcement
- User provisioning/de-provisioning

**Technology**: MSAL Python + python-jose

**Flow**:
1. User redirected to Azure AD
2. User authenticates (credentials + MFA)
3. Azure AD returns authorization code
4. Backend exchanges code for tokens
5. Access token (30 min) + refresh token (7 days) issued
6. Refresh token rotation on each use

**Security**:
- Tokens signed with RS256 (asymmetric)
- Refresh tokens hashed in database
- Session tracking for revocation
- IP validation (optional)

### 3. Model Router Service

**Purpose**: Intelligent selection of AI model for generation requests

**Responsibilities**:
- Analyze prompt complexity
- Check department budget and preferences
- Evaluate model availability and SLA
- Select optimal model based on criteria
- Implement fallback logic

**Technology**: Python with custom selection algorithm

**Selection Criteria**:
```python
class ModelSelectionCriteria:
    prompt_complexity: float       # 0-1 score
    required_quality: str          # low, medium, high
    max_cost: Decimal              # Budget constraint
    required_sla: float            # 99.0-99.99
    commercial_use: bool           # License requirement
    department_preferences: Dict
    historical_success_rate: float # Per-model performance
```

**Algorithm**:
```
1. Filter models by hard constraints
   - Budget available?
   - SLA requirements met?
   - Commercial license needed?

2. Score remaining models
   - Quality score (0-100)
   - Cost score (0-100)
   - Reliability score (0-100)
   - Speed score (0-100)

3. Apply department weights
   - Cost-optimized: Cost 50%, Quality 30%, Speed 20%
   - Quality-focused: Quality 60%, Cost 20%, Speed 20%
   - Balanced: Equal weights

4. Select highest-scoring model
5. If failure, try next highest-scoring model
```

### 4. Generation Service

**Purpose**: Orchestrate image generation workflow

**Responsibilities**:
- Validate and sanitize prompts
- PII detection (Presidio)
- Content moderation (Azure Content Safety)
- Call selected model provider
- Handle retries and timeouts
- Post-processing (watermarking, metadata)
- Store results

**Technology**: Celery (async task queue)

**Workflow**:
```
1. Pre-Generation (< 1s)
   ├── Validate prompt (length, format)
   ├── PII detection scan
   ├── Content safety check
   ├── Budget check
   └── Enqueue generation task

2. Generation (5-30s)
   ├── Model selection
   ├── API call with retry logic
   ├── Progress updates via WebSocket
   └── Handle timeouts (60s max)

3. Post-Generation (< 2s)
   ├── NSFW content check
   ├── Metadata injection
   ├── Image optimization
   ├── Upload to Blob Storage
   ├── Update database
   └── Send webhook notification
```

**Error Handling**:
- Retry failed requests (max 3 attempts)
- Exponential backoff (2s, 4s, 8s)
- Fallback to alternative model
- Detailed error logging
- User-friendly error messages

### 5. Cost Management Service

**Purpose**: Track and enforce budget constraints

**Responsibilities**:
- Real-time cost tracking
- Budget enforcement (hard/soft/warn modes)
- Cost allocation by department/user
- Spend analytics and forecasting
- Alert generation (80%, 90%, 100% thresholds)

**Technology**: Python + Azure SQL

**Data Model**:
```sql
CREATE TABLE department_budgets (
    id UUID PRIMARY KEY,
    department_id UUID,
    monthly_budget_aud DECIMAL(10,2),
    current_spend_aud DECIMAL(10,2),
    reset_date DATE,
    enforcement_mode VARCHAR(10) CHECK (enforcement_mode IN ('hard', 'soft', 'warn'))
);

CREATE TABLE cost_events (
    id UUID PRIMARY KEY,
    generation_id UUID,
    department_id UUID,
    user_id UUID,
    model_used VARCHAR(50),
    cost_aud DECIMAL(10,4),
    timestamp TIMESTAMP
);
```

**Budget Enforcement**:
```python
def check_budget(department_id, estimated_cost):
    budget = get_department_budget(department_id)

    if budget.current_spend + estimated_cost > budget.monthly_budget:
        if budget.enforcement_mode == 'hard':
            raise BudgetExceededError()
        elif budget.enforcement_mode == 'soft':
            log_warning()  # Allow but log
        elif budget.enforcement_mode == 'warn':
            send_alert()  # Notify but allow

    # Pre-allocate cost
    reserve_budget(department_id, estimated_cost)
```

### 6. Audit Logger Service

**Purpose**: Comprehensive, immutable audit trail

**Responsibilities**:
- Log all user actions
- Security event logging
- Compliance audit trail
- Real-time log streaming to Cosmos DB
- Log retention enforcement (7 years)

**Technology**: Cosmos DB (append-only container)

**Log Schema**:
```json
{
  "id": "uuid",
  "timestamp": "ISO 8601",
  "event_type": "enum",
  "user_id": "uuid",
  "user_email": "string",
  "action": "string",
  "resource_type": "string",
  "resource_id": "uuid",
  "ip_address": "string",
  "user_agent": "string",
  "request_id": "uuid",
  "status": "success | failure",
  "error_message": "string | null",
  "metadata": {
    "prompt": "string (encrypted)",
    "model": "string",
    "cost_aud": "decimal"
  }
}
```

**Indexed Fields**:
- `user_id`
- `timestamp`
- `event_type`
- `resource_id`

**Partition Key**: `user_id` (for efficient user-specific queries)

### 7. User Management Service

**Purpose**: CRUD operations for users and roles

**Responsibilities**:
- User provisioning/de-provisioning
- Role assignment
- Department membership
- Profile management
- Access review reporting

**Technology**: FastAPI + SQLAlchemy

**API Endpoints**:
```
POST   /api/v1/admin/users              # Create user
GET    /api/v1/admin/users              # List users
GET    /api/v1/admin/users/{id}         # Get user
PATCH  /api/v1/admin/users/{id}         # Update user
DELETE /api/v1/admin/users/{id}         # Deactivate user
POST   /api/v1/admin/users/{id}/roles   # Assign role
POST   /api/v1/admin/users/bulk         # Bulk import (CSV)
```

---

## Data Architecture

### Database Schema (Azure SQL)

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) and accompanying Mermaid diagrams for detailed entity-relationship diagrams.

### Data Flow

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ 1. Submit generation request
       ▼
┌──────────────────┐
│  API Gateway     │
│  (Validation)    │
└──────┬───────────┘
       │ 2. Enqueue task
       ▼
┌──────────────────┐
│  Celery Queue    │
│  (Redis)         │
└──────┬───────────┘
       │ 3. Worker picks up task
       ▼
┌──────────────────────────────────────┐
│  Generation Service                  │
│  ├── PII Detection (Presidio)        │
│  ├── Content Safety Check            │
│  ├── Model Selection                 │
│  ├── API Call (OpenAI/Replicate/etc)│
│  └── Post-processing                 │
└──────┬───────────────────────────────┘
       │ 4. Store image
       ▼
┌──────────────────┐      ┌────────────────┐      ┌──────────────┐
│  Blob Storage    │      │  Azure SQL     │      │  Cosmos DB   │
│  (Image file)    │◄─────┤  (Metadata)    │      │  (Audit log) │
└──────────────────┘      └────────────────┘      └──────────────┘
       │
       │ 5. Return CDN URL
       ▼
┌──────────────────┐
│  User            │
│  (Image display) │
└──────────────────┘
```

---

## Integration Architecture

### External Model Providers

| Provider | Model | Protocol | Auth Method | Timeout | Retry Strategy |
|----------|-------|----------|-------------|---------|----------------|
| Azure OpenAI | DALL-E 3 | REST | API Key (Key Vault) | 60s | 3 attempts, exponential backoff |
| Replicate | SD XL | REST | API Token | 60s | 3 attempts, exponential backoff |
| Adobe | Firefly | REST | OAuth 2.0 | 60s | 3 attempts, exponential backoff |
| Azure Cognitive | Azure AI | REST | Subscription Key | 60s | 3 attempts, exponential backoff |

### Integration Patterns

**Circuit Breaker Pattern**:
```python
class ModelProviderCircuitBreaker:
    max_failures = 5
    timeout = 60  # seconds
    half_open_attempts = 3

    states = ['CLOSED', 'OPEN', 'HALF_OPEN']
```

**Retry with Exponential Backoff**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type(ProviderError)
)
def call_model_provider(provider, prompt):
    # API call logic
    pass
```

---

## Security Architecture

See [SECURITY_ARCHITECTURE.md](SECURITY_ARCHITECTURE.md) for comprehensive security design.

**Key Security Controls**:
- Defense in Depth (7 layers)
- Zero Trust (explicit verification)
- Encryption at rest and in transit
- MFA enforcement
- RBAC with least privilege
- Immutable audit logs
- Regular security scanning
- Incident response automation

---

## Deployment Architecture

### Kubernetes Architecture (AKS)

```
┌───────────────────────────────────────────────────────────┐
│              AKS Cluster (Australia East)                 │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Node Pool: System (2-4 nodes, Standard_D4s_v3)│     │
│  │  • kube-system pods                             │     │
│  │  • ingress-nginx controller                     │     │
│  │  • cert-manager                                 │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Node Pool: App (3-20 nodes, Standard_D8s_v3)  │     │
│  │  • FastAPI pods (4 workers each)                │     │
│  │  • Frontend pods (Nginx)                        │     │
│  │  • Auto-scaling: CPU > 70% or memory > 80%      │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Node Pool: Workers (2-10 nodes, Standard_F8s) │     │
│  │  • Celery worker pods                           │     │
│  │  • CPU-optimized for image processing          │     │
│  │  • Auto-scaling: Queue depth > 100              │     │
│  └─────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────┘
```

### Deployment Strategy

**Blue-Green Deployment**:
1. Deploy new version to "green" environment
2. Run smoke tests on green
3. Gradually shift traffic (10%, 25%, 50%, 100%)
4. Monitor error rates and latency
5. Rollback if error rate > 1% or latency > 500ms

**Rollback Procedure**:
```bash
# Instant rollback to previous version
kubectl rollout undo deployment/api-gateway -n production

# Rollback to specific revision
kubectl rollout undo deployment/api-gateway --to-revision=5 -n production
```

---

## Scalability & Performance

### Horizontal Scaling

| Component | Min Replicas | Max Replicas | Scale Trigger |
|-----------|-------------|--------------|---------------|
| API Gateway | 3 | 20 | CPU > 70% or RPS > 500 |
| Frontend | 2 | 10 | CPU > 60% |
| Celery Workers | 2 | 10 | Queue depth > 100 |
| Redis | 1 | 3 | Memory > 80% |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time | < 200ms | P95 |
| Image Generation | < 30s | P90 |
| Database Query | < 50ms | P95 |
| CDN Cache Hit Rate | > 90% | Average |
| Uptime | 99.95% | Monthly |

### Caching Strategy

```
┌─────────────────────────────────────────────────────┐
│                   CACHING LAYERS                     │
├─────────────────────────────────────────────────────┤
│  Layer 1: Browser Cache (7 days)                    │
│  • Static assets (JS, CSS, images)                  │
│  • Cache-Control: public, max-age=604800            │
├─────────────────────────────────────────────────────┤
│  Layer 2: CDN Cache (30 days)                       │
│  • Generated images                                 │
│  • Immutable URLs with version hash                 │
├─────────────────────────────────────────────────────┤
│  Layer 3: Redis Cache (1 hour)                      │
│  • Session data                                     │
│  • User preferences                                 │
│  • Model availability status                        │
├─────────────────────────────────────────────────────┤
│  Layer 4: Database Query Cache (5 minutes)          │
│  • User roles and permissions                       │
│  • Department settings                              │
│  • Model provider configurations                    │
└─────────────────────────────────────────────────────┘
```

---

## Disaster Recovery

### RTO and RPO Targets

| Tier | RTO (Recovery Time Objective) | RPO (Recovery Point Objective) |
|------|------------------------------|--------------------------------|
| Critical (User data, audit logs) | 1 hour | 5 minutes |
| High (Generated images) | 4 hours | 1 hour |
| Medium (Analytics data) | 24 hours | 24 hours |

### Backup Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    BACKUP SCHEDULE                       │
├─────────────────────────────────────────────────────────┤
│  Azure SQL Database                                      │
│  • Automated backups: Every 5-10 minutes (transaction log)
│  • Full backup: Weekly                                   │
│  • Differential backup: Daily                            │
│  • Retention: 35 days (point-in-time restore)            │
├─────────────────────────────────────────────────────────┤
│  Cosmos DB                                               │
│  • Continuous backup mode enabled                        │
│  • Point-in-time restore: Last 30 days                   │
│  • Geo-replication: Australia Southeast (automatic)      │
├─────────────────────────────────────────────────────────┤
│  Blob Storage                                            │
│  • GRS (Geo-Redundant Storage) enabled                   │
│  • Soft delete: 30 days                                  │
│  • Versioning: Enabled                                   │
│  • Snapshot: Weekly                                      │
├─────────────────────────────────────────────────────────┤
│  Key Vault                                               │
│  • Soft delete: 90 days                                  │
│  • Purge protection: Enabled                             │
│  • Backup: Daily export to secure storage               │
└─────────────────────────────────────────────────────────┘
```

### Failover Procedure

```
Scenario: Primary Region (Australia East) Failure

Step 1: Detect Failure (< 5 minutes)
• Azure Monitor alerts triggered
• Health check failures detected
• Traffic rerouted by Azure Front Door

Step 2: Activate DR Site (< 30 minutes)
• Promote Australia Southeast to primary
• Update DNS records (if needed)
• Scale up DR AKS cluster
• Promote read-replica to writable

Step 3: Verify Services (< 15 minutes)
• Run smoke tests
• Verify data integrity
• Check audit log continuity
• Validate authentication

Step 4: Full Operation (< 1 hour total)
• Monitor error rates
• Notify stakeholders
• Document incident
• Plan return to primary region
```

---

## Monitoring & Observability

### Observability Stack

```
┌──────────────────────────────────────────────────────┐
│                   OBSERVABILITY                       │
├──────────────────────────────────────────────────────┤
│  Metrics (Azure Monitor + Application Insights)      │
│  • Request rate, latency, error rate                 │
│  • Resource utilization (CPU, memory, disk)          │
│  • Custom business metrics (generations/day)         │
├──────────────────────────────────────────────────────┤
│  Logs (Azure Log Analytics)                          │
│  • Structured JSON logs                              │
│  • Centralized aggregation                           │
│  • KQL queries for analysis                          │
├──────────────────────────────────────────────────────┤
│  Traces (Application Insights Distributed Tracing)   │
│  • Request correlation IDs                           │
│  • End-to-end transaction tracing                    │
│  • Dependency mapping                                │
├──────────────────────────────────────────────────────┤
│  Alerting (Azure Monitor Alerts)                     │
│  • Error rate > 1%                                   │
│  • Latency P95 > 500ms                               │
│  • Budget utilization > 90%                          │
│  • Security anomalies                                │
└──────────────────────────────────────────────────────┘
```

### Key Metrics Dashboard

| Metric Category | Specific Metrics | Alert Threshold |
|----------------|------------------|-----------------|
| **Availability** | Uptime %, Health check success rate | < 99.95% |
| **Performance** | API latency P50/P95/P99, Generation time | P95 > 200ms |
| **Errors** | 4xx rate, 5xx rate, Generation failures | > 1% |
| **Capacity** | CPU%, Memory%, Disk%, Queue depth | > 80% |
| **Business** | Generations/day, Cost/image, User registrations | Anomaly detection |
| **Security** | Failed auth attempts, PII detections, Budget violations | > 10 failures/min |

### Dashboards

1. **Executive Dashboard**: High-level KPIs, uptime, costs
2. **Operations Dashboard**: Resource utilization, alerts, incidents
3. **Security Dashboard**: Auth events, PII detections, vulnerabilities
4. **Business Dashboard**: Usage trends, department analytics, ROI

---

## Appendices

### A. Technology Decision Records

See `docs/architecture/adr/` for detailed Architecture Decision Records (ADRs).

### B. Compliance Mappings

See `docs/compliance/iso27001-mapping.md` for ISO 27001 control mappings.

### C. API Documentation

See `docs/api/openapi.yaml` for complete OpenAPI specification.

### D. Runbooks

See `docs/runbooks/` for operational procedures.

---

**Document Control**

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Author | DonatelloAI Architecture Team |
| Date | 2025-11-17 |
| Review Date | 2026-02-17 |
| Classification | CONFIDENTIAL |
| Approvers | CTO, CISO, Compliance Officer |

---

**Change Log**

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-17 | 1.0 | Architecture Team | Initial comprehensive architecture document |
