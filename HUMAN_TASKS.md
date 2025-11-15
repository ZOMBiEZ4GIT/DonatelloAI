# Human Tasks - Enterprise Image Generation Platform

> **Last Updated**: 2025-11-15
> **Session**: Initial Setup
> **Status**: 🟡 Awaiting Azure Prerequisites

---

## ⚠️ IMMEDIATE PREREQUISITES (REQUIRED BEFORE DEVELOPMENT)

These tasks must be completed by humans before development can proceed:

### Azure Infrastructure Setup
- [ ] **Create Azure AD tenant** for development environment
  - Tenant name: `[YOUR-ORG]-eig-dev`
  - Region: Australia East
  - Estimated time: 30 minutes

- [ ] **Set up Azure subscription** with cost alerts
  - Subscription type: Pay-As-You-Go or Enterprise Agreement
  - Set cost alert at: $100/day, $500/week, $1500/month
  - Estimated time: 1 hour

- [ ] **Register application in Azure AD**
  - Application name: `EIG-Platform-Dev`
  - Redirect URIs: `https://localhost:8000/auth/callback` (dev)
  - Required permissions: User.Read, Directory.Read.All
  - Estimated time: 20 minutes

- [ ] **Create Azure Key Vault instance**
  - Name: `eig-keyvault-dev-aue`
  - Region: Australia East
  - SKU: Standard (Premium for production)
  - Enable soft delete: Yes (90-day retention)
  - Estimated time: 15 minutes

### Development Tools
- [ ] **Configure Azure DevOps project**
  - Project name: `EIG-Platform`
  - Repository: Git
  - Work item process: Agile
  - Estimated time: 30 minutes

- [ ] **Set up local development environment**
  - Install Azure CLI: `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`
  - Install Docker Desktop: Required for local AKS testing
  - Install kubectl: For Kubernetes management
  - Install Terraform: Infrastructure as Code
  - Estimated time: 1 hour

### API Keys and Credentials
- [ ] **Obtain API keys for model providers**
  - [ ] OpenAI API key (for DALL-E 3)
    - Sign up at: https://platform.openai.com/
    - Consider Azure OpenAI Service for compliance
  - [ ] Replicate API key (for Stable Diffusion XL)
    - Sign up at: https://replicate.com/
  - [ ] Adobe Firefly API access
    - Apply at: https://developer.adobe.com/firefly-services/
    - Note: May require enterprise agreement
  - [ ] Azure AI Services key
    - Create via Azure Portal > Cognitive Services
  - Estimated time: 2-3 hours (approval times vary)

---

## 🔧 DURING DEVELOPMENT - HUMAN DECISIONS NEEDED

### Checkpoint 1: Authentication Architecture ⏸️
**STATUS**: Waiting for human confirmation

Before implementing authentication, we need decisions on:

1. **Azure Entra ID Configuration**
   - ❓ Should we use Azure AD B2C for external users or keep it internal-only with standard Entra ID?
   - ❓ Do we need guest user access for external contractors?
   - ❓ Should we integrate with existing corporate Azure AD or create standalone tenant?

2. **MFA Enforcement**
   - ❓ Mandatory MFA for all users or role-based (e.g., admins only)?
   - ❓ Acceptable MFA methods: Authenticator app only, or also SMS/phone?
   - ❓ Grace period for MFA setup (e.g., 7 days) or enforce immediately?

3. **Session Management**
   - ❓ Session timeout: 30 minutes, 1 hour, or 8 hours?
   - ❓ Allow concurrent sessions from different IPs?
   - ❓ Require re-authentication for sensitive actions (e.g., budget changes)?

4. **RBAC Hierarchy**
   - ❓ Confirm 5-tier role structure: Super Admin → Org Admin → Dept Manager → Power User → Standard User?
   - ❓ Should Power Users have approval workflow or direct access?
   - ❓ Custom roles needed for specific clients?

### Checkpoint 2: Model Integration Strategy
**STATUS**: Not yet reached

Decisions needed:
- [ ] **API Key Storage**
  - ❓ Store in Azure Key Vault with managed identity access?
  - ❓ Separate Key Vaults per environment (dev/staging/prod)?
  - ❓ Automatic key rotation frequency (30/60/90 days)?

- [ ] **Rate Limiting Approach**
  - ❓ Per-user limits: 10/hour (free), 100/hour (standard), unlimited (enterprise)?
  - ❓ Per-department daily limits enforced?
  - ❓ Burst allowance for sudden spikes?

- [ ] **Cost Allocation Method**
  - ❓ Real-time cost tracking or batch updates (hourly/daily)?
  - ❓ Cost allocation by: user, department, project, or combination?
  - ❓ Chargeback model for internal departments?

- [ ] **Model Provider Strategy**
  - ❓ Use Azure OpenAI Service exclusively or mix direct API + Azure?
  - ❓ Replicate vs Azure ML for Stable Diffusion hosting?
  - ❓ Fallback priority order for models?

### Checkpoint 3: Data Persistence Layer
**STATUS**: Not yet reached

Decisions needed:
- [ ] **Database Selection**
  - ❓ Azure SQL vs PostgreSQL on Azure for metadata?
  - ❓ Cosmos DB (NoSQL) vs Azure SQL for audit logs?
  - ❓ Table Storage for high-volume metrics?

- [ ] **Blob Storage Strategy**
  - ❓ Hot/cool/archive tiers based on image age (30/60/90 days)?
  - ❓ CDN caching strategy for frequently accessed images?
  - ❓ Separate storage accounts per department for isolation?

- [ ] **Encryption Strategy**
  - ❓ Customer-managed keys (CMK) or Microsoft-managed?
  - ❓ Client-side encryption for prompts containing sensitive data?
  - ❓ Separate encryption keys per customer organization?

- [ ] **Backup and Retention**
  - ❓ RPO (Recovery Point Objective): 1 hour, 4 hours, 24 hours?
  - ❓ RTO (Recovery Time Objective): 2 hours, 8 hours, 24 hours?
  - ❓ Geo-redundant storage (GRS) for disaster recovery?

### Checkpoint 4: Compliance Framework
**STATUS**: Not yet reached

Decisions needed:
- [ ] **PII Detection**
  - ❓ Build custom PII detection or use Azure Cognitive Services?
  - ❓ PII sensitivity level: Names only, or include addresses/phone numbers?
  - ❓ Block generation on PII detection or warn and allow override?

- [ ] **Audit Log Immutability**
  - ❓ Use Cosmos DB with append-only mode?
  - ❓ Azure Blob Storage with immutability policies?
  - ❓ Third-party audit log service for compliance?

- [ ] **ISO 27001 Priority Controls**
  - ❓ Which controls to implement in Phase 1 (MVP)?
  - ❓ External auditor selected for certification?
  - ❓ Timeline for certification: 6 months, 9 months, 12 months?

- [ ] **Data Residency**
  - ❓ Strict Australia-only or allow Southeast Asia for DR?
  - ❓ Model providers that process data outside Australia acceptable?
  - ❓ Data transfer agreements needed?

### Checkpoint 5: Cost Management System
**STATUS**: Not yet reached

Decisions needed:
- [ ] **Billing Model**
  - ❓ Prepaid credits vs post-paid monthly invoicing?
  - ❓ Department budget: hard stop or soft limit with alerts?
  - ❓ Overage handling: queue requests or reject immediately?

- [ ] **Budget Controls**
  - ❓ Budget approval workflow: single approver or dual control?
  - ❓ Budget adjustment frequency: monthly, quarterly?
  - ❓ Automatic budget rollover or reset each period?

- [ ] **Cost Allocation Granularity**
  - ❓ Track costs by: user, project, cost center, or all three?
  - ❓ Activity-based costing for shared services?
  - ❓ Chargeback reports: real-time or monthly batch?

- [ ] **Overage Policies**
  - ❓ Allow departments to exceed with approval workflow?
  - ❓ Emergency override for critical requests?
  - ❓ Overage penalty (e.g., 20% surcharge) to discourage abuse?

---

## 🚀 PRODUCTION READINESS CHECKLIST

### Infrastructure
- [ ] **DNS and Networking**
  - [ ] Configure DNS records for custom domain
  - [ ] Set up Azure Front Door with WAF rules
  - [ ] Configure DDoS protection (Azure DDoS Standard)
  - [ ] SSL/TLS certificates purchased and uploaded
  - [ ] CDN configuration for image delivery

- [ ] **Security Hardening**
  - [ ] Upload SSL certificates to Key Vault
  - [ ] Configure Azure Firewall rules
  - [ ] Set up VPN for secure admin access
  - [ ] Configure Network Security Groups (NSGs)
  - [ ] Enable Azure Defender for all services

- [ ] **Monitoring and Alerting**
  - [ ] Set up Azure Monitor alerts
  - [ ] Configure Application Insights
  - [ ] Set up Azure Sentinel SIEM
  - [ ] Create runbooks for common incidents
  - [ ] Configure PagerDuty/OpsGenie integration

### Access and Identity
- [ ] **RBAC and Permissions**
  - [ ] Create service principals for deployment
  - [ ] Configure Privileged Identity Management (PIM)
  - [ ] Set up Just-In-Time (JIT) access
  - [ ] Review and approve RBAC permissions
  - [ ] Disable default admin accounts

- [ ] **Audit and Compliance**
  - [ ] Enable Azure Policy enforcement
  - [ ] Configure compliance reporting
  - [ ] Set up automated compliance checks
  - [ ] Create audit log retention policies

### Data and Backup
- [ ] **Backup Policies**
  - [ ] Configure automated database backups
  - [ ] Set up geo-redundant storage
  - [ ] Test restore procedures
  - [ ] Document RTO/RPO commitments

- [ ] **Disaster Recovery**
  - [ ] Create DR runbooks
  - [ ] Set up failover regions
  - [ ] Test disaster recovery procedures
  - [ ] Document business continuity plan

### Cost Management
- [ ] **Budget Controls**
  - [ ] Set up Azure Cost Management alerts
  - [ ] Configure budget thresholds ($100/day, $500/week, $2000/month)
  - [ ] Set up cost anomaly detection
  - [ ] Create monthly cost reports

---

## 📋 PRE-LAUNCH ACTIVITIES

### Testing and Validation
- [ ] **Security Testing**
  - [ ] Arrange penetration testing
  - [ ] OWASP Top 10 vulnerability scan
  - [ ] Container security scanning
  - [ ] Dependency vulnerability audit
  - [ ] Static code analysis (SAST)
  - [ ] Dynamic code analysis (DAST)

- [ ] **Performance Testing**
  - [ ] Load testing at scale (10,000 concurrent users)
  - [ ] Stress testing for failure modes
  - [ ] Endurance testing (24-hour runs)
  - [ ] Spike testing for traffic bursts

- [ ] **Compliance Audit**
  - [ ] ISO 27001 auditor selection
  - [ ] Pre-audit gap analysis
  - [ ] Stage 1 audit (documentation)
  - [ ] Stage 2 audit (implementation)
  - [ ] Remediate audit findings

### Legal and Business
- [ ] **Legal Review**
  - [ ] Terms of service review
  - [ ] Privacy policy review
  - [ ] SLA agreements review
  - [ ] Insurance policy review (E&O, cyber liability)
  - [ ] Model provider contract review

- [ ] **Operational Readiness**
  - [ ] Create compliance documentation templates
  - [ ] Incident response team formation
  - [ ] Customer support process setup
  - [ ] Training materials creation
  - [ ] Security awareness training

---

## 📊 TRACKING METRICS

### Development Progress
- **Specification Review**: ✅ Complete
- **Project Structure**: ⏳ In Progress
- **Core Authentication**: ⏸️ Awaiting Checkpoint 1 Approval
- **Model Integration**: 🔴 Not Started
- **Compliance Framework**: 🔴 Not Started
- **Production Deployment**: 🔴 Not Started

### Checkpoint Status
1. ⏸️ **Authentication Architecture**: Awaiting human decisions
2. 🔴 **Model Integration Strategy**: Not reached
3. 🔴 **Data Persistence Layer**: Not reached
4. 🔴 **Compliance Framework**: Not reached
5. 🔴 **Cost Management System**: Not reached

---

## 💡 NOTES FOR HUMAN REVIEWERS

### Important Context
- This platform handles **sensitive corporate data** - security is non-negotiable
- **Cost overruns** could be catastrophic - implement multiple safeguards
- **ISO 27001 certification** is a hard requirement for enterprise sales
- **Australian data sovereignty** is legally required for government clients
- Platform will be **externally audited** - all controls must be demonstrable

### Decision-Making Framework
For each checkpoint, consider:
1. **Security implications**: Does this introduce vulnerabilities?
2. **Cost impact**: Does this affect operational costs?
3. **Compliance**: Does this meet ISO 27001/23053 requirements?
4. **Scalability**: Will this work at 10,000 concurrent users?
5. **Auditability**: Can we prove compliance to auditors?

### Contact Points
- **Technical Decisions**: Senior Platform Architect
- **Security Decisions**: CISO or Security Lead
- **Compliance Decisions**: Legal/Compliance Officer
- **Cost Decisions**: CFO or Finance Controller

---

**🚦 CURRENT STATUS**: Awaiting Checkpoint 1 decisions on authentication architecture before proceeding with implementation.
