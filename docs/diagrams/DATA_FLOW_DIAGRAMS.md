# 📊 Data Flow Diagrams
## Enterprise Image Generation Platform (DonatelloAI)

> **Version**: 1.0
> **Date**: 2025-11-17
> **Format**: Mermaid Diagrams

---

## Table of Contents

1. [Authentication Flow](#authentication-flow)
2. [Image Generation Flow](#image-generation-flow)
3. [Budget Enforcement Flow](#budget-enforcement-flow)
4. [User Management Flow](#user-management-flow)
5. [Audit Logging Flow](#audit-logging-flow)
6. [Model Selection Flow](#model-selection-flow)
7. [Error Handling Flow](#error-handling-flow)
8. [Webhook Notification Flow](#webhook-notification-flow)

---

## Authentication Flow

### User Login Flow (OAuth 2.0 + OpenID Connect)

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Frontend
    participant API Gateway
    participant Auth Service
    participant Azure AD
    participant Database
    participant Audit Logger

    User->>Browser: Click "Login with Microsoft"
    Browser->>Frontend: Initiate login
    Frontend->>Azure AD: Redirect to login page
    Note over Azure AD: Prompt for credentials + MFA
    User->>Azure AD: Enter credentials + MFA code
    Azure AD->>Azure AD: Validate credentials
    Azure AD->>Azure AD: Check MFA
    Azure AD-->>Frontend: Return authorization code

    Frontend->>API Gateway: POST /auth/callback {code}
    API Gateway->>Auth Service: Exchange code for tokens
    Auth Service->>Azure AD: Token exchange request
    Azure AD-->>Auth Service: access_token, id_token, refresh_token

    Auth Service->>Auth Service: Validate tokens
    Auth Service->>Database: Lookup or create user
    Database-->>Auth Service: User record

    Auth Service->>Database: Create session record
    Auth Service->>Audit Logger: Log successful login
    Audit Logger->>Cosmos DB: Write audit log

    Auth Service-->>API Gateway: Session token (JWT)
    API Gateway-->>Frontend: Set httpOnly cookie
    Frontend-->>Browser: Redirect to dashboard
    Browser->>User: Display application
```

### Token Refresh Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant API Gateway
    participant Auth Service
    participant Database
    participant Azure AD

    User->>Frontend: Action requiring auth
    Frontend->>API Gateway: Request with expired access token
    API Gateway->>Auth Service: Validate token
    Auth Service-->>API Gateway: 401 Token Expired

    API Gateway->>Frontend: 401 Unauthorized
    Frontend->>Frontend: Check refresh token in cookie
    Frontend->>API Gateway: POST /auth/refresh {refresh_token}

    API Gateway->>Auth Service: Validate refresh token
    Auth Service->>Database: Lookup session
    Database-->>Auth Service: Session record

    alt Valid session
        Auth Service->>Azure AD: Exchange refresh token
        Azure AD-->>Auth Service: New access_token + refresh_token

        Auth Service->>Database: Update session (rotate refresh token)
        Auth Service->>Database: Update last_used_at

        Auth Service-->>API Gateway: New tokens
        API Gateway-->>Frontend: Set new cookies
        Frontend->>Frontend: Retry original request
        Frontend->>User: Success
    else Invalid or expired session
        Auth Service-->>API Gateway: 403 Forbidden
        API Gateway-->>Frontend: Session expired
        Frontend->>User: Redirect to login
    end
```

---

## Image Generation Flow

### Complete Generation Workflow

```mermaid
flowchart TD
    A[User submits prompt] --> B{Authenticated?}
    B -->|No| C[Redirect to login]
    B -->|Yes| D[Validate prompt]

    D --> E{Valid format?}
    E -->|No| F[Return 400 Bad Request]
    E -->|Yes| G[PII Detection Scan]

    G --> H{PII detected?}
    H -->|Yes| I[Return 403 PII Error]
    H -->|No| J[Content Safety Check]

    J --> K{Safe content?}
    K -->|No| L[Return 403 Content Violation]
    K -->|Yes| M[Check Department Budget]

    M --> N{Budget available?}
    N -->|No| O[Return 402 Budget Exceeded]
    N -->|Yes| P[Reserve budget allocation]

    P --> Q[Enqueue Celery task]
    Q --> R[Return 202 Accepted + task_id]
    R --> S[WebSocket: generation.started]

    S --> T[Model Selection Algorithm]
    T --> U[Call Model Provider API]

    U --> V{Success?}
    V -->|No| W{Retry attempts < 3?}
    W -->|Yes| X[Exponential backoff]
    X --> U
    W -->|No| Y{Fallback model available?}
    Y -->|Yes| Z[Select fallback model]
    Z --> U
    Y -->|No| AA[Return 500 Generation Failed]

    V -->|Yes| AB[NSFW Content Check]
    AB --> AC{Safe?}
    AC -->|No| AD[Flag image + notify admin]
    AC -->|Yes| AE[Image Post-processing]

    AE --> AF[Add metadata EXIF]
    AF --> AG[Optimize file size]
    AG --> AH[Upload to Blob Storage]
    AH --> AI[Generate CDN URL]
    AI --> AJ[Update database record]
    AJ --> AK[Record actual cost]
    AK --> AL[Release budget reservation]
    AL --> AM[Send webhook notification]
    AM --> AN[WebSocket: generation.completed]
    AN --> AO[Return image URL to user]
```

### Detailed Generation Sequence

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant API Gateway
    participant PII Service
    participant Content Safety
    participant Budget Service
    participant Celery Queue
    participant Worker
    participant Model Router
    participant Model Provider
    participant Blob Storage
    participant Database
    participant Audit Logger
    participant WebSocket

    User->>Frontend: Submit generation request
    Frontend->>API Gateway: POST /api/v1/generate {prompt, settings}

    API Gateway->>PII Service: Scan prompt for PII
    PII Service-->>API Gateway: No PII detected

    API Gateway->>Content Safety: Check content safety
    Content Safety-->>API Gateway: Safe content

    API Gateway->>Budget Service: Check budget
    Budget Service->>Database: Query department budget
    Database-->>Budget Service: Budget available
    Budget Service->>Database: Reserve estimated cost
    Budget Service-->>API Gateway: Budget reserved

    API Gateway->>Celery Queue: Enqueue task
    Celery Queue-->>API Gateway: task_id
    API Gateway-->>Frontend: 202 Accepted {task_id}

    Frontend->>WebSocket: Subscribe to updates

    Worker->>Celery Queue: Poll for tasks
    Celery Queue-->>Worker: Generation task

    Worker->>WebSocket: generation.started
    WebSocket-->>Frontend: Update progress bar

    Worker->>Model Router: Select optimal model
    Model Router->>Model Router: Analyze criteria
    Model Router-->>Worker: Selected model: DALL-E 3

    Worker->>Model Provider: POST /generate {prompt}
    Note over Model Provider: 5-30 seconds processing

    loop Progress updates
        Model Provider-->>Worker: Progress 25%
        Worker->>WebSocket: generation.progress {25%}
        WebSocket-->>Frontend: Update progress bar
    end

    Model Provider-->>Worker: Image binary data

    Worker->>Worker: NSFW content check
    Worker->>Worker: Add metadata
    Worker->>Worker: Optimize image

    Worker->>Blob Storage: Upload image
    Blob Storage-->>Worker: CDN URL

    Worker->>Database: Update generation record
    Worker->>Budget Service: Record actual cost
    Budget Service->>Database: Update department spend

    Worker->>Audit Logger: Log generation event
    Audit Logger->>Cosmos DB: Write audit log

    Worker->>WebSocket: generation.completed {url}
    WebSocket-->>Frontend: Display image

    Frontend->>User: Show generated image
```

---

## Budget Enforcement Flow

### Budget Check and Enforcement

```mermaid
flowchart TD
    A[Generation request received] --> B[Lookup department]
    B --> C[Get department budget config]

    C --> D{Enforcement mode?}

    D -->|hard| E[Calculate current spend]
    E --> F{Spend + estimated_cost > budget?}
    F -->|Yes| G[Reject request]
    F -->|No| H[Reserve allocation]

    D -->|soft| I[Calculate current spend]
    I --> J{Spend + estimated_cost > budget?}
    J -->|Yes| K[Log warning]
    K --> L[Allow request]
    J -->|No| L

    D -->|warn| M[Calculate current spend]
    M --> N{Spend + estimated_cost > budget?}
    N -->|Yes| O[Send alert to manager]
    O --> P[Allow request]
    N -->|No| P

    G --> Q[Return 402 Payment Required]
    H --> R[Proceed with generation]
    L --> R
    P --> R

    R --> S[Generation completes]
    S --> T[Record actual cost]
    T --> U{Actual cost != estimated?}
    U -->|Yes| V[Adjust budget allocation]
    U -->|No| W[Confirm allocation]

    V --> X[Update department spend]
    W --> X
    X --> Y{Threshold exceeded?}

    Y -->|80%| Z[Send warning email]
    Y -->|90%| AA[Send urgent email]
    Y -->|100%| AB[Lock department + notify]
    Y -->|< 80%| AC[No alert]

    Z --> AD[Continue monitoring]
    AA --> AD
    AB --> AD
    AC --> AD
```

### Budget Alert Flow

```mermaid
sequenceDiagram
    participant Generation Service
    participant Budget Service
    participant Database
    participant Alert Service
    participant Email Service
    participant Dept Manager
    participant Org Admin

    Generation Service->>Budget Service: Record cost ($0.08)
    Budget Service->>Database: UPDATE department_spend
    Database-->>Budget Service: New total: $950 / $1000

    Budget Service->>Budget Service: Calculate threshold
    Note over Budget Service: 950 / 1000 = 95%

    Budget Service->>Alert Service: Trigger 90% alert

    par Send to Department Manager
        Alert Service->>Email Service: Send email
        Email Service->>Dept Manager: Budget 95% utilized
    and Send to Org Admin
        Alert Service->>Email Service: Send email
        Email Service->>Org Admin: Dept X at 95%
    and Log alert
        Alert Service->>Database: Record alert sent
    end

    Note over Dept Manager: Receives email notification
    Dept Manager->>Dashboard: View budget details

    alt Increase budget
        Dept Manager->>Budget Service: Increase budget to $1500
        Budget Service->>Database: UPDATE budget
        Budget Service->>Alert Service: Cancel alerts
    else Reduce usage
        Dept Manager->>Users: Send guidance email
    else Do nothing
        Note over Dept Manager: Wait until month reset
    end
```

---

## User Management Flow

### User Provisioning Workflow

```mermaid
flowchart TD
    A[Admin creates user] --> B{Bulk import or single?}

    B -->|Single| C[Enter user details]
    B -->|Bulk| D[Upload CSV file]

    C --> E[Validate email format]
    D --> F[Parse CSV]
    F --> G[Validate all rows]

    G --> H{All valid?}
    H -->|No| I[Return validation errors]
    H -->|Yes| J[Process users]

    E --> K{Valid email?}
    K -->|No| L[Return 400 error]
    K -->|Yes| M[Check for duplicates]

    M --> N{User exists?}
    N -->|Yes| O[Return 409 Conflict]
    N -->|No| P[Check Azure AD]

    P --> Q{User in Azure AD?}
    Q -->|No| R[Create Azure AD user]
    Q -->|Yes| S[Get Azure AD ID]

    R --> T[Send welcome email]
    S --> U[Create database record]
    T --> U

    U --> V[Assign to department]
    V --> W[Assign default role]
    W --> X{MFA required?}

    X -->|Yes| Y[Set MFA grace period]
    X -->|No| Z[Mark account active]

    Y --> AA[Send MFA setup email]
    AA --> AB[Log user creation]
    Z --> AB

    J --> AC[Create all users in batch]
    AC --> AB

    AB --> AD[Audit log entry]
    AD --> AE[Return success]
```

### User Deactivation Flow

```mermaid
sequenceDiagram
    actor Admin
    participant Admin Dashboard
    participant API Gateway
    participant User Service
    participant Database
    participant Session Service
    participant Audit Logger
    participant Email Service
    participant User

    Admin->>Admin Dashboard: Click "Deactivate User"
    Admin Dashboard->>Admin Dashboard: Confirm action
    Admin->>Admin Dashboard: Confirm deactivation

    Admin Dashboard->>API Gateway: DELETE /api/v1/users/{id}
    API Gateway->>User Service: Deactivate user request

    User Service->>Database: SELECT user record
    Database-->>User Service: User details

    User Service->>User Service: Validate permissions
    Note over User Service: Admin can only deactivate<br/>users in their scope

    User Service->>Database: UPDATE users SET is_active=false
    User Service->>Session Service: Revoke all sessions

    Session Service->>Database: UPDATE user_sessions SET revoked=true
    Session Service->>Redis: DELETE session keys

    User Service->>Audit Logger: Log deactivation
    Audit Logger->>Cosmos DB: Write audit log

    User Service->>Email Service: Send notification
    Email Service->>User: Account deactivated email

    User Service-->>API Gateway: 200 OK
    API Gateway-->>Admin Dashboard: Success message
    Admin Dashboard->>Admin: Display confirmation

    Note over User: Next API request will fail<br/>with 401 Unauthorized
```

---

## Audit Logging Flow

### Comprehensive Audit Trail

```mermaid
flowchart TD
    A[Any user action] --> B{Action type}

    B -->|Authentication| C[Login/Logout event]
    B -->|Authorization| D[Permission check]
    B -->|Data access| E[Read operation]
    B -->|Data modification| F[Create/Update/Delete]
    B -->|Admin action| G[User/Department management]
    B -->|Generation| H[Image creation]
    B -->|Budget| I[Cost event]

    C --> J[Collect metadata]
    D --> J
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J

    J --> K[Enrich with context]
    K --> L[User ID]
    K --> M[IP address]
    K --> N[User agent]
    K --> O[Request ID]
    K --> P[Timestamp UTC]
    K --> Q[Resource details]

    L --> R[Format as JSON]
    M --> R
    N --> R
    O --> R
    P --> R
    Q --> R

    R --> S{Sensitive data?}
    S -->|Yes| T[Encrypt fields]
    S -->|No| U[Keep plaintext]

    T --> V[Write to Cosmos DB]
    U --> V

    V --> W{Write successful?}
    W -->|No| X[Retry with backoff]
    W -->|Yes| Y[Acknowledge]

    X --> Z{Retries < 3?}
    Z -->|Yes| V
    Z -->|No| AA[Log to local file]
    AA --> AB[Alert operations]

    Y --> AC[Audit log persisted]
    AC --> AD{Retention policy}

    AD -->|7 years| AE[Immutable storage]
    AD -->|After 7 years| AF[Automated deletion]
```

### Audit Log Query Flow

```mermaid
sequenceDiagram
    actor Auditor
    participant Admin Dashboard
    participant API Gateway
    participant Audit Service
    participant Cosmos DB
    participant Cache

    Auditor->>Admin Dashboard: Navigate to Audit Logs
    Admin Dashboard->>API Gateway: GET /api/v1/audit/logs?filters

    API Gateway->>Audit Service: Query logs
    Audit Service->>Cache: Check cache

    alt Cache hit
        Cache-->>Audit Service: Cached results
        Audit Service-->>API Gateway: Return logs
    else Cache miss
        Audit Service->>Cosmos DB: Query with filters
        Note over Cosmos DB: Efficient partition key query<br/>using user_id or date range
        Cosmos DB-->>Audit Service: Log entries

        Audit Service->>Audit Service: Decrypt sensitive fields
        Audit Service->>Audit Service: Apply RBAC filters
        Note over Audit Service: Dept managers only see<br/>their department logs

        Audit Service->>Cache: Store results (5 min TTL)
        Audit Service-->>API Gateway: Return filtered logs
    end

    API Gateway-->>Admin Dashboard: Display logs
    Admin Dashboard->>Auditor: Render audit table

    alt Export request
        Auditor->>Admin Dashboard: Click "Export to CSV"
        Admin Dashboard->>API Gateway: POST /api/v1/audit/export
        API Gateway->>Audit Service: Generate export
        Audit Service->>Cosmos DB: Query all matching logs
        Audit Service->>Audit Service: Convert to CSV
        Audit Service-->>API Gateway: CSV file
        API Gateway-->>Admin Dashboard: Download CSV
        Admin Dashboard->>Auditor: Save file
    end
```

---

## Model Selection Flow

### Intelligent Model Selection Algorithm

```mermaid
flowchart TD
    A[Generation request] --> B[Extract requirements]

    B --> C[Parse prompt]
    C --> D[Analyze complexity]
    D --> E{Complexity score}

    E -->|High 0.8-1.0| F[High quality needed]
    E -->|Medium 0.4-0.7| G[Balanced approach]
    E -->|Low 0.0-0.3| H[Cost-optimized]

    F --> I[Filter models]
    G --> I
    H --> I

    I --> J{Department preferences}
    J -->|Quality-focused| K[Quality weight: 60%]
    J -->|Cost-focused| L[Cost weight: 50%]
    J -->|Balanced| M[Equal weights]

    K --> N[Check constraints]
    L --> N
    M --> N

    N --> O{Budget available?}
    O -->|No| P[Return budget error]
    O -->|Yes| Q{Commercial use?}

    Q -->|Yes| R[Filter: Commercial license]
    Q -->|No| S[All models eligible]

    R --> T[Calculate model scores]
    S --> T

    T --> U[Score: Quality 0-100]
    T --> V[Score: Cost 0-100]
    T --> W[Score: Reliability 0-100]
    T --> X[Score: Speed 0-100]

    U --> Y[Apply department weights]
    V --> Y
    W --> Y
    X --> Y

    Y --> Z[Rank models]
    Z --> AA[Select highest-ranked]

    AA --> AB{Model available?}
    AB -->|Yes| AC[Return selected model]
    AB -->|No| AD[Select next-best model]
    AD --> AB

    AC --> AE[Log selection decision]
    AE --> AF[Proceed to generation]
```

### Model Fallback Strategy

```mermaid
sequenceDiagram
    participant Worker
    participant Model Router
    participant DALL-E 3
    participant SD XL
    participant Azure AI
    participant Audit Logger

    Worker->>Model Router: Select model
    Model Router-->>Worker: Primary: DALL-E 3

    Worker->>DALL-E 3: Generate image
    Note over DALL-E 3: Request times out (60s)
    DALL-E 3-->>Worker: 504 Gateway Timeout

    Worker->>Audit Logger: Log failure
    Worker->>Worker: Increment retry count (1/3)

    alt Retry primary model
        Worker->>DALL-E 3: Retry with backoff
        DALL-E 3-->>Worker: 503 Service Unavailable
        Worker->>Worker: Increment retry count (2/3)
    end

    Worker->>Model Router: Request fallback model
    Model Router->>Model Router: Check availability
    Model Router-->>Worker: Fallback: Stable Diffusion XL

    Worker->>SD XL: Generate image
    Note over SD XL: Successful generation
    SD XL-->>Worker: Image binary

    Worker->>Audit Logger: Log fallback success
    Audit Logger->>Cosmos DB: model_used: sdxl, fallback: true

    Worker->>Worker: Continue post-processing
```

---

## Error Handling Flow

### Global Error Handling

```mermaid
flowchart TD
    A[Request received] --> B{Try block}

    B -->|Success| C[Return response]
    B -->|Exception| D{Exception type?}

    D -->|ValidationError| E[400 Bad Request]
    D -->|AuthenticationError| F[401 Unauthorized]
    D -->|AuthorizationError| G[403 Forbidden]
    D -->|ResourceNotFoundError| H[404 Not Found]
    D -->|BudgetExceededError| I[402 Payment Required]
    D -->|PIIDetectedError| J[403 Forbidden + PII warning]
    D -->|ModelUnavailableError| K[503 Service Unavailable]
    D -->|DatabaseError| L[500 Internal Server Error]
    D -->|Unknown| M[500 Internal Server Error]

    E --> N{Environment?}
    F --> N
    G --> N
    H --> N
    I --> N
    J --> N
    K --> N
    L --> N
    M --> N

    N -->|Production| O[Sanitized error message]
    N -->|Development| P[Detailed error + stack trace]

    O --> Q[Log to Application Insights]
    P --> Q

    Q --> R{Error severity?}
    R -->|Critical| S[Page operations immediately]
    R -->|High| T[Create incident ticket]
    R -->|Medium| U[Log for review]
    R -->|Low| V[Metrics only]

    S --> W[Send alert]
    T --> W
    U --> X[Store in monitoring]
    V --> X

    W --> X
    X --> Y[Return error response to client]
```

### Retry Logic with Exponential Backoff

```mermaid
sequenceDiagram
    participant Caller
    participant Service
    participant External API
    participant Logger

    Caller->>Service: Request
    Service->>External API: API Call (Attempt 1)
    External API-->>Service: 503 Service Unavailable

    Service->>Logger: Log failure
    Service->>Service: Calculate backoff: 2s
    Note over Service: Wait 2 seconds

    Service->>External API: API Call (Attempt 2)
    External API-->>Service: Timeout

    Service->>Logger: Log failure
    Service->>Service: Calculate backoff: 4s
    Note over Service: Wait 4 seconds

    Service->>External API: API Call (Attempt 3)
    External API-->>Service: 200 OK + Data

    Service->>Logger: Log success (3rd attempt)
    Service-->>Caller: Return data

    Note over Service: If all 3 attempts fail,<br/>try fallback or return error
```

---

## Webhook Notification Flow

### Webhook Event Delivery

```mermaid
sequenceDiagram
    participant Generation Service
    participant Database
    participant Webhook Service
    participant Queue
    participant Worker
    participant Customer Endpoint
    participant Retry Store

    Generation Service->>Generation Service: Generation completed
    Generation Service->>Database: Get user webhook config
    Database-->>Generation Service: webhook_url, secret, events

    Generation Service->>Webhook Service: Trigger webhook
    Webhook Service->>Webhook Service: Construct payload
    Webhook Service->>Webhook Service: Sign with HMAC-SHA256

    Webhook Service->>Queue: Enqueue webhook task
    Queue-->>Webhook Service: Acknowledged

    Webhook Service-->>Generation Service: Webhook queued

    Worker->>Queue: Poll for webhook tasks
    Queue-->>Worker: Webhook task

    Worker->>Customer Endpoint: POST webhook
    Note over Customer Endpoint: Customer's API endpoint

    alt Success response
        Customer Endpoint-->>Worker: 200 OK
        Worker->>Database: Mark webhook delivered
        Worker->>Database: Record delivery time
    else Failure response
        Customer Endpoint-->>Worker: 500 Internal Server Error
        Worker->>Retry Store: Schedule retry
        Note over Retry Store: Retry schedule:<br/>1m, 5m, 15m, 1h, 6h, 24h

        Retry Store-->>Worker: Acknowledged

        loop Retry attempts
            Note over Worker: Wait for retry time
            Worker->>Customer Endpoint: POST webhook (retry)
            alt Success
                Customer Endpoint-->>Worker: 200 OK
                Worker->>Database: Mark delivered
            else Max retries exceeded
                Worker->>Database: Mark failed
                Worker->>Alert Service: Notify admin
            end
        end
    end
```

---

## System Integration Dataflow

### End-to-End Data Flow

```mermaid
graph LR
    subgraph User Layer
        A[Web Browser]
        B[Mobile App Future]
    end

    subgraph Edge Layer
        C[Azure Front Door]
        D[WAF]
    end

    subgraph API Layer
        E[API Management]
        F[API Gateway]
    end

    subgraph Service Layer
        G[Auth Service]
        H[Generation Service]
        I[Model Router]
        J[Cost Service]
        K[Audit Service]
    end

    subgraph Data Layer
        L[(Azure SQL)]
        M[(Cosmos DB)]
        N[Blob Storage]
        O[Redis Cache]
        P[Key Vault]
    end

    subgraph External Layer
        Q[Azure OpenAI]
        R[Replicate]
        S[Adobe API]
    end

    A --> C
    B -.-> C
    C --> D
    D --> E
    E --> F

    F --> G
    F --> H
    F --> K

    G --> L
    G --> O
    G --> P

    H --> I
    H --> J
    H --> N

    I --> Q
    I --> R
    I --> S

    J --> L
    K --> M

    Q -.->|Image Data| H
    R -.->|Image Data| H
    S -.->|Image Data| H
```

---

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Author | DonatelloAI Architecture Team |
| Date | 2025-11-17 |
| Review Date | 2026-02-17 |
| Classification | CONFIDENTIAL |

---

**Usage Notes**:
- All diagrams are rendered using Mermaid syntax
- View in GitHub, GitLab, or any Mermaid-compatible viewer
- Export to PNG/SVG using Mermaid CLI or online tools
- Update diagrams when architecture changes

---

**Related Documentation**:
- [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)
- [API Specification](../api/openapi.yaml)
- [Database Schema](../architecture/DATABASE_SCHEMA.md)
- [Security Architecture](../architecture/SECURITY_ARCHITECTURE.md)
