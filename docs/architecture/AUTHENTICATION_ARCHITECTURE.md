# 🔐 Authentication Architecture Design
## Enterprise Image Generation Platform

> **Status**: 🟡 AWAITING CHECKPOINT 1 APPROVAL
> **Version**: 1.0
> **Date**: 2025-11-15
> **ISO 27001 Controls**: A.9.2, A.9.4

---

## ⚠️ CHECKPOINT 1: CRITICAL DECISIONS REQUIRED

Before implementing authentication, **human approval is required** for the following architectural decisions. These choices will have significant impact on security, compliance, and user experience.

---

## 📋 Decision Points

### 1. Azure Entra ID Configuration Approach

**Question**: Should we use Azure AD B2C for external users or keep it internal-only with standard Entra ID?

**Options**:

#### Option A: Standard Azure Entra ID (Internal Only) ✅ RECOMMENDED
**Scope**: Enterprise employees only
- ✅ Simpler architecture
- ✅ Lower cost ($0/user for basic, ~$6/user/month for premium)
- ✅ Direct integration with corporate Azure AD
- ✅ Native MFA support
- ❌ No external/guest user support
- ❌ Limited customization of login experience

**Use case**: Platform for internal enterprise use only

#### Option B: Azure AD B2C (Internal + External)
**Scope**: Enterprise employees + external partners/customers
- ✅ Supports external users (B2C scenarios)
- ✅ Customizable login/signup flows
- ✅ Social identity providers (Google, Microsoft, etc.)
- ✅ White-label branding
- ❌ More complex architecture
- ❌ Higher cost (~$0.05 per MAU + premium features)
- ❌ Additional governance complexity

**Use case**: Platform offered as SaaS to external customers

#### Option C: Hybrid (Entra ID + B2C)
**Scope**: Both internal and external with clear separation
- ✅ Best of both worlds
- ✅ Clear tenant separation
- ❌ Most complex architecture
- ❌ Higher operational overhead
- ❌ Highest cost

**Use case**: Enterprise with future SaaS ambitions

**RECOMMENDATION**: **Option A (Standard Entra ID)** for Phase 1
- Align with spec requirement: "Enterprise authentication via Azure Entra ID"
- Simplify compliance and security auditing
- Can add B2C later if external access needed

**Human Decision Required**: Which option aligns with business model?
- [ ] Option A: Internal only (recommended for MVP)
- [ ] Option B: External users supported
- [ ] Option C: Hybrid approach

---

### 2. Multi-Factor Authentication (MFA) Strategy

**Question**: How should MFA be enforced across different user roles?

**Options**:

#### Option A: Mandatory MFA for All Users ✅ RECOMMENDED
- ✅ Maximum security
- ✅ ISO 27001 best practice
- ✅ Simplest policy to implement
- ✅ No exceptions means no audit complexity
- ❌ Potential user resistance
- ❌ Support overhead for MFA setup

**Configuration**:
```python
MFA_ENFORCEMENT = {
    "super_admin": "required",
    "org_admin": "required",
    "dept_manager": "required",
    "power_user": "required",
    "standard_user": "required",
}
MFA_GRACE_PERIOD_DAYS = 7  # Time to set up MFA
ALLOWED_MFA_METHODS = ["authenticator_app", "phone"]  # No SMS
```

#### Option B: Role-Based MFA (Tiered)
- ✅ Balanced approach
- ✅ Less user friction for low-privilege users
- ❌ More complex policy
- ❌ Potential security gaps

**Configuration**:
```python
MFA_ENFORCEMENT = {
    "super_admin": "required",
    "org_admin": "required",
    "dept_manager": "required",
    "power_user": "optional",  # Encouraged but not required
    "standard_user": "optional",
}
```

#### Option C: Conditional Access (Context-Aware)
- ✅ Most sophisticated
- ✅ Azure AD Premium feature
- ✅ MFA based on risk signals
- ❌ Requires Azure AD Premium P1/P2
- ❌ Complex to configure and audit

**Factors**:
- IP address (require MFA from outside corporate network)
- Device compliance (require MFA from unmanaged devices)
- Location (require MFA from high-risk countries)
- Sign-in risk (Azure AD Identity Protection)

**RECOMMENDATION**: **Option A (Mandatory for All)** for maximum security
- ISO 27001 A.9.4.2 compliance
- Australian Cyber Security Centre (ACSC) recommendation
- Reduces attack surface significantly

**Human Decision Required**: MFA enforcement approach?
- [ ] Option A: Mandatory for all users (recommended)
- [ ] Option B: Role-based enforcement
- [ ] Option C: Conditional access (requires Azure AD Premium P2)

**Additional MFA Questions**:
- [ ] Acceptable MFA methods: Authenticator app only, or also SMS/phone?
- [ ] MFA grace period for new users: 7 days, 14 days, or enforce immediately?
- [ ] Remember MFA for trusted devices: Yes (30 days) or No (require every time)?

---

### 3. Session Management Strategy

**Question**: How should user sessions be managed for security and usability?

**Options**:

#### Option A: Short-Lived Sessions (Secure) ✅ RECOMMENDED
**Configuration**:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
REQUIRE_REAUTH_FOR_SENSITIVE_OPS = True
ALLOW_CONCURRENT_SESSIONS = False
```

- ✅ Maximum security (ISO 27001 A.9.4.2)
- ✅ Limits exposure window if token compromised
- ✅ Forces re-auth for sensitive operations
- ❌ Users must log in more frequently
- ❌ More token refresh requests

**Use case**: High-security environments, financial services

#### Option B: Balanced Sessions (Moderate)
**Configuration**:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
REQUIRE_REAUTH_FOR_SENSITIVE_OPS = True
ALLOW_CONCURRENT_SESSIONS = True  # Max 3 devices
```

- ✅ Better user experience
- ✅ Still reasonably secure
- ❌ Slightly larger attack window

**Use case**: Standard enterprise applications

#### Option C: Long-Lived Sessions (Convenient)
**Configuration**:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = 90
REQUIRE_REAUTH_FOR_SENSITIVE_OPS = False
ALLOW_CONCURRENT_SESSIONS = True  # Unlimited
```

- ✅ Best user experience
- ❌ Security risk if device compromised
- ❌ May not pass ISO 27001 audit

**NOT RECOMMENDED** for this platform

**RECOMMENDATION**: **Option A (Short-Lived)** for ISO 27001 compliance
- 30-minute access tokens
- 7-day refresh tokens
- Re-authentication required for budget changes, user management
- Single concurrent session per user (or max 2 devices)

**Human Decision Required**: Session management approach?
- [ ] Option A: Short-lived sessions (recommended for compliance)
- [ ] Option B: Balanced approach
- [ ] Session timeout: 30 minutes, 1 hour, or 8 hours?
- [ ] Allow concurrent sessions from different IPs: Yes/No?
- [ ] Require re-authentication for sensitive actions: Yes/No?

---

### 4. Role-Based Access Control (RBAC) Hierarchy

**Question**: Confirm the 5-tier role structure and permissions?

**Proposed Hierarchy**:

```
┌─────────────────────────────────────────────────────────┐
│                    SUPER ADMIN                           │
│  • Platform-wide configuration                           │
│  • All organization access                               │
│  • Model provider management                             │
│  • Security settings                                     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 ORGANIZATION ADMIN                       │
│  • Organization-wide settings                            │
│  • Create/manage departments                             │
│  • View all department budgets                           │
│  • Compliance reporting                                  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 DEPARTMENT MANAGER                       │
│  • Department budget management                          │
│  • Add/remove department users                           │
│  • View department analytics                             │
│  • Configure department defaults                         │
└─────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
┌───────────────────────────┐  ┌───────────────────────────┐
│      POWER USER            │  │     STANDARD USER         │
│  • Unlimited generation    │  │  • Rate-limited generation│
│  • Batch operations        │  │  • Basic features only    │
│  • Advanced features       │  │  • No batch operations    │
│  • API access              │  │  • Web interface only     │
└───────────────────────────┘  └───────────────────────────┘
```

**Permission Matrix**:

| Action | Super Admin | Org Admin | Dept Manager | Power User | Standard User |
|--------|-------------|-----------|--------------|------------|---------------|
| Generate images | ✅ | ✅ | ✅ | ✅ | ✅ |
| Batch generation | ✅ | ✅ | ✅ | ✅ | ❌ |
| API access | ✅ | ✅ | ✅ | ✅ | ❌ |
| View own history | ✅ | ✅ | ✅ | ✅ | ✅ |
| View dept analytics | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage dept budget | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage dept users | ✅ | ✅ | ✅ | ❌ | ❌ |
| View all orgs | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage models | ✅ | ❌ | ❌ | ❌ | ❌ |
| Configure security | ✅ | ❌ | ❌ | ❌ | ❌ |
| View audit logs | ✅ | ✅ | ✅ | ❌ | ❌ |

**Human Decision Required**:
- [ ] Approve 5-tier role structure: Yes/No?
- [ ] Should Power Users have approval workflow or direct unlimited access?
- [ ] Custom roles needed for specific clients: Yes/No?
- [ ] Should Dept Managers see detailed user activity or just aggregates?

---

## 🏗️ Proposed Technical Architecture

### High-Level Flow

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ 1. Access protected resource
       ▼
┌─────────────────────────────────────────┐
│     Azure Front Door + WAF              │
│  • DDoS protection                      │
│  • Geo-filtering (Australia focus)      │
└──────┬──────────────────────────────────┘
       │ 2. Forward to API Gateway
       ▼
┌─────────────────────────────────────────┐
│     FastAPI Application                 │
│  • Check for JWT in Authorization header│
└──────┬──────────────────────────────────┘
       │ 3a. No token → Redirect to login
       │
       │ 3b. Has token → Validate
       ▼
┌─────────────────────────────────────────┐
│   Token Validation Service              │
│  • Verify JWT signature                 │
│  • Check expiration                     │
│  • Validate issuer/audience             │
└──────┬──────────────────────────────────┘
       │ 4a. Invalid → 401 Unauthorized
       │
       │ 4b. Valid → Extract user claims
       ▼
┌─────────────────────────────────────────┐
│   Authorization Service (RBAC)          │
│  • Load user role from database         │
│  • Check permission for requested action│
└──────┬──────────────────────────────────┘
       │ 5a. Forbidden → 403 Forbidden
       │
       │ 5b. Authorized → Execute request
       ▼
┌─────────────────────────────────────────┐
│   Business Logic                        │
│  • Generate image                       │
│  • Manage users                         │
│  • Update budgets                       │
└─────────────────────────────────────────┘
```

### Authentication Flow (OAuth 2.0 + OpenID Connect)

```
┌─────────┐                                      ┌──────────────┐
│ User    │                                      │  Azure AD    │
└────┬────┘                                      └──────┬───────┘
     │                                                  │
     │ 1. Click "Login with Microsoft"                 │
     ├─────────────────────────────────────────────────▶
     │                                                  │
     │ 2. Redirect to Azure AD login page              │
     ◀─────────────────────────────────────────────────┤
     │                                                  │
     │ 3. Enter credentials + MFA                       │
     ├─────────────────────────────────────────────────▶
     │                                                  │
     │ 4. Consent screen (first time only)              │
     ◀─────────────────────────────────────────────────┤
     │                                                  │
     │ 5. Redirect back with authorization code         │
     ◀─────────────────────────────────────────────────┤
     │                                                  │
     ▼                                                  │
┌──────────────┐                                       │
│ EIG Platform │                                       │
│   Backend    │                                       │
└──────┬───────┘                                       │
     │                                                  │
     │ 6. Exchange auth code for tokens                 │
     ├─────────────────────────────────────────────────▶
     │                                                  │
     │ 7. Return access_token + id_token + refresh_token│
     ◀─────────────────────────────────────────────────┤
     │                                                  │
     │ 8. Validate tokens, create session               │
     │                                                  │
     │ 9. Store tokens securely (httpOnly cookie)       │
     │                                                  │
     │ 10. Redirect to dashboard                        │
     ▼                                                  │
```

### Token Structure

**Access Token (JWT)**:
```json
{
  "iss": "https://login.microsoftonline.com/{tenant_id}/v2.0",
  "sub": "azure_ad_user_id",
  "aud": "eig-platform-api",
  "exp": 1700000000,
  "iat": 1699998000,
  "email": "user@organization.com.au",
  "name": "John Doe",
  "roles": ["department_manager"],
  "department_id": "uuid",
  "mfa_verified": true
}
```

**Refresh Token** (opaque string):
- Stored securely in httpOnly, secure cookie
- Used to obtain new access tokens
- Rotated on each use (security best practice)

### Database Schema

```sql
-- Users table (Azure SQL)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_ad_id VARCHAR(255) UNIQUE NOT NULL,  -- Azure AD object ID
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    department_id UUID REFERENCES departments(id),
    role VARCHAR(50) NOT NULL CHECK (role IN (
        'super_admin',
        'org_admin',
        'dept_manager',
        'power_user',
        'standard_user'
    )),
    is_active BOOLEAN DEFAULT true,
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_grace_period_expires_at TIMESTAMP,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_users_azure_ad_id ON users(azure_ad_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_department_id ON users(department_id);
CREATE INDEX idx_users_role ON users(role);

-- Sessions table (for token tracking and revocation)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,  -- Hashed refresh token
    device_info JSONB,  -- User agent, IP, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT false,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(255)
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_refresh_token_hash ON user_sessions(refresh_token_hash);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
```

---

## 🔒 Security Measures

### 1. Token Security
- ✅ Access tokens stored in memory only (no localStorage)
- ✅ Refresh tokens in httpOnly, secure, SameSite cookies
- ✅ Short token lifetimes (30 min access, 7 day refresh)
- ✅ Token rotation on refresh (one-time use)
- ✅ Secure token storage (encrypted at rest)

### 2. Transport Security
- ✅ TLS 1.3 enforced
- ✅ HSTS headers (max-age=31536000)
- ✅ Certificate pinning for critical endpoints
- ✅ No mixed content allowed

### 3. Session Security
- ✅ Session fixation protection
- ✅ CSRF tokens for state-changing operations
- ✅ IP address validation (optional)
- ✅ Device fingerprinting (optional)
- ✅ Automatic logout on inactivity

### 4. Audit Logging
All authentication events logged to Cosmos DB:
- Login attempts (success/failure)
- MFA challenges
- Token refreshes
- Session terminations
- Permission denials
- Password changes
- Role changes

---

## 🎯 Implementation Plan

### Phase 1: Basic Authentication (Week 1)
- [ ] Azure AD app registration
- [ ] OAuth 2.0 flow implementation
- [ ] JWT validation
- [ ] Basic session management
- [ ] Login/logout endpoints

### Phase 2: RBAC (Week 2)
- [ ] Database schema implementation
- [ ] Role assignment logic
- [ ] Permission checking middleware
- [ ] Admin user management endpoints

### Phase 3: MFA & Hardening (Week 3)
- [ ] MFA enforcement logic
- [ ] Grace period handling
- [ ] Token rotation
- [ ] Session revocation
- [ ] Audit logging integration

### Phase 4: Testing & Documentation (Week 4)
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests
- [ ] Security testing
- [ ] API documentation
- [ ] Runbooks

---

## 📋 Compliance Checklist

### ISO 27001 Controls
- ✅ **A.9.2.1**: User registration and de-registration
- ✅ **A.9.2.2**: User access provisioning
- ✅ **A.9.2.3**: Management of privileged access rights
- ✅ **A.9.2.4**: Management of secret authentication information
- ✅ **A.9.2.5**: Review of user access rights
- ✅ **A.9.2.6**: Removal or adjustment of access rights
- ✅ **A.9.4.1**: Information access restriction
- ✅ **A.9.4.2**: Secure log-on procedures
- ✅ **A.9.4.3**: Password management system

### Australian Privacy Act 1988
- ✅ User consent for data collection
- ✅ Secure storage of personal information
- ✅ Data breach notification procedures

### ACSC Essential Eight
- ✅ Multi-factor authentication
- ✅ Application control (RBAC)
- ✅ Patch management (Azure AD managed)
- ✅ User application hardening

---

## 🚦 CHECKPOINT 1: SUMMARY OF REQUIRED DECISIONS

Before proceeding with implementation, please confirm:

1. **Azure AD Strategy**:
   - [ ] Standard Entra ID (internal only) ← RECOMMENDED
   - [ ] Azure AD B2C (external users)
   - [ ] Hybrid approach

2. **MFA Enforcement**:
   - [ ] Mandatory for all users ← RECOMMENDED
   - [ ] Role-based enforcement
   - [ ] Conditional access (requires Premium P2)
   - [ ] Allowed MFA methods: Authenticator app / SMS / Both?
   - [ ] Grace period: 7 days / 14 days / Immediate?

3. **Session Management**:
   - [ ] Short-lived (30 min) ← RECOMMENDED
   - [ ] Balanced (60 min)
   - [ ] Allow concurrent sessions: Yes/No?
   - [ ] Require re-auth for sensitive operations: Yes/No?

4. **RBAC Structure**:
   - [ ] Approve 5-tier role hierarchy: Yes/No?
   - [ ] Power Users need approval workflow: Yes/No?
   - [ ] Custom roles needed: Yes/No?

---

**Once approved, implementation will begin immediately. Estimated time: 3-4 weeks to production-ready.**

**Questions or concerns? Please provide feedback before approval.**
