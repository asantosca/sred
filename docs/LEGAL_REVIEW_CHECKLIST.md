# Legal Review Checklist for BC Legal Tech

**Date Created**: November 9, 2025
**Purpose**: Guide for legal counsel reviewing BC Legal Tech's legal documentation

---

## Overview

BC Legal Tech is an AI-powered legal document intelligence platform for British Columbia law firms. We provide semantic search, document management, and AI chat assistance for legal professionals handling confidential client information.

**Critical Context**: Our platform processes confidential legal documents and client information, making legal compliance and professional responsibility paramount.

---

## Documents for Review

All legal documents are located in `/marketing/src/app/`:

1. **Privacy Policy** (`privacy/page.tsx`) - 11 sections, ~2,500 words
2. **Terms of Service** (`terms/page.tsx`) - 14 sections, ~4,500 words
3. **Cookie Policy** (`cookies/page.tsx`) - 9 sections, ~2,800 words

**Status**: All are comprehensive templates requiring customization and legal review.

---

## Key Areas Requiring Legal Attention

### 1. Privacy Policy (CRITICAL)

**BC/Canadian Privacy Law Compliance:**
- [ ] PIPEDA (Personal Information Protection and Electronic Documents Act) compliance
- [ ] BC FIPPA (Freedom of Information and Protection of Privacy Act) considerations
- [ ] Privacy Commissioner of Canada requirements
- [ ] Law Society of BC confidentiality rules integration

**AI Processing Disclosures:**
- [ ] OpenAI API usage (embeddings for search)
- [ ] Anthropic Claude API usage (chat responses)
- [ ] Third-party AI data processing agreements
- [ ] Opt-out enforcement from AI model training
- [ ] Data residency (preference for Canadian servers)

**Key Questions:**
- Is our disclosure about AI processing sufficient?
- Do we need explicit consent for AI processing of legal documents?
- Are our third-party data processing safeguards adequate?
- Should we add specific provisions for solicitor-client privilege?

### 2. Terms of Service (HIGH PRIORITY)

**Liability Limitations:**
- [ ] AI accuracy disclaimers (Section 8.2)
- [ ] Professional responsibility disclaimers
- [ ] Limitation of liability caps (Section 9)
- [ ] Force majeure provisions

**Law Firm Specific Issues:**
- [ ] Professional conduct rules integration
- [ ] Ethical obligations acknowledgment
- [ ] Malpractice insurance implications
- [ ] Conflicts of interest disclosures

**Intellectual Property:**
- [ ] User content ownership (Section 5.1)
- [ ] Limited license scope for AI processing
- [ ] Data deletion upon termination

**Key Questions:**
- Are our liability limitations enforceable under BC law?
- Do we need specific language about Law Society of BC rules?
- Should we require users to have their own professional indemnity insurance?
- Is our AI disclaimer strong enough given legal profession standards?

### 3. Cookie Policy

**GDPR & PIPEDA Alignment:**
- [ ] Cookie consent mechanisms
- [ ] Granular preference controls
- [ ] Do Not Track signal support
- [ ] Data retention periods

**Key Questions:**
- Is our cookie consent implementation GDPR-compliant?
- Do we need separate consent for analytics vs. functional cookies?

### 4. CASL Compliance (Canada's Anti-Spam Legislation)

**Express Consent Implementation:**
- [x] Explicit checkbox for commercial electronic messages (CEMs)
- [x] Clear description of what emails they'll receive
- [x] Unsubscribe mechanism disclosure
- [x] Consent timestamp tracking in database
- [x] Separate consent from general Privacy Policy acceptance

**Waitlist Form CASL Consent:**
The waitlist form now includes:
- Required checkbox for marketing emails
- Clear language: "I consent to receive commercial electronic messages from BC Legal Tech, including product updates, beta program invitations, feature announcements, and promotional offers"
- Explicit mention of unsubscribe rights
- CASL explanation note
- Database tracking of `consent_marketing` (boolean) and `consent_date` (timestamp)

**What's Covered:**
✅ Express consent for marketing emails
✅ Clear identification of sender (BC Legal Tech)
✅ Unsubscribe mechanism (mentioned in consent, needs implementation in emails)
✅ Purpose clearly stated (product updates, beta invites, features, promos)
✅ Record of consent (timestamp in database)

**What's NOT Covered (Needs Implementation):**
- [ ] Unsubscribe link in actual marketing emails
- [ ] Preference center for email types
- [ ] Consent withdrawal mechanism in account settings
- [ ] Confirmation email after signup (transactional, exempt from CASL)

**Transactional Emails (Exempt from CASL consent):**
- Password reset emails
- Account activation/verification emails
- Billing/invoice emails
- Service status notifications
- Security alerts

These do NOT require consent and should be sent even if user hasn't consented to marketing.

**Key Questions:**
- Is our consent language sufficiently clear?
- Should we provide granular consent options (e.g., separate consent for different email types)?
- Do we need a double opt-in confirmation email?
- Should we include consent withdrawal instructions in Privacy Policy?

### 5. Data Processing Agreement (TO BE CREATED)

**Enterprise Requirements:**
- [ ] Data processor vs. controller definitions
- [ ] Sub-processor disclosures
- [ ] Security measures and audits
- [ ] Breach notification procedures
- [ ] Data return/deletion upon termination

**Law Firm Specific:**
- [ ] Solicitor-client privilege protection
- [ ] Conflicts screening procedures
- [ ] Multi-tenant isolation guarantees
- [ ] Regulatory compliance (Law Society rules)

---

## Specific Legal Risks to Address

### High Priority Risks:

1. **AI Hallucinations / Inaccurate Advice**
   - Current: General disclaimer in Section 8.2
   - Question: Is this sufficient given legal context?
   - Consider: Explicit "not legal advice" warnings on every AI response?

2. **Solicitor-Client Privilege**
   - Current: General confidentiality provisions
   - Question: Do we need explicit privilege protection clauses?
   - Consider: Waiver of privilege concerns when using third-party AI?

3. **Data Breach Liability**
   - Current: Limitation of liability in Section 9
   - Question: Is liability cap enforceable for breach involving client data?
   - Consider: Mandatory cybersecurity insurance requirements?

4. **Multi-Tenant Data Isolation**
   - Current: General security representations
   - Question: Should we provide explicit guarantees about firm isolation?
   - Consider: Technical audit rights for enterprise clients?

5. **Professional Conduct Rules**
   - Current: User responsibility for ethical compliance
   - Question: Do we need to reference specific Law Society of BC rules?
   - Consider: Mandatory acknowledgment of professional obligations?

### Medium Priority Risks:

6. **Cross-Border Data Transfer**
   - OpenAI/Anthropic may process data in US
   - Standard contractual clauses needed?

7. **Third-Party Service Failures**
   - AWS, AI providers, payment processors
   - Adequate disclaimers for third-party failures?

8. **Subscription Cancellation / Refunds**
   - Pro-rated refund policy fair?
   - Early termination rights?

---

## Jurisdiction-Specific Considerations

### British Columbia Specific:
- [ ] Law Society of BC rules and regulations
- [ ] BC Privacy Commissioner requirements
- [ ] BC court jurisdiction clauses (Section 12.3)
- [ ] BC Consumer Protection Act compliance

### Federal (Canada):
- [ ] PIPEDA compliance
- [ ] Anti-Spam Legislation (CASL) for marketing emails
- [ ] Competition Act considerations
- [ ] Federal court jurisdiction for IP disputes

---

## Questions for Legal Counsel

### Privacy & Data Protection:
1. Should we obtain separate consent for AI processing, beyond general terms acceptance?
2. Do we need a Data Protection Impact Assessment (DPIA) for AI processing?
3. Should we designate a Data Protection Officer (DPO)?
4. Are our data retention periods (90 days post-termination) adequate?

### Professional Responsibility:
5. Should we require law firms to obtain their own clients' consent before uploading?
6. Do we need specific provisions about conflicts of interest screening?
7. Should we prohibit certain document types (e.g., sealed documents, privileged comms)?
8. Do we need mandatory reporting of suspected ethical violations?

### Liability & Risk Management:
9. Are our liability caps enforceable given the nature of legal work?
10. Should we require users to maintain professional indemnity insurance?
11. Do we need mandatory arbitration clauses?
12. Should we have separate terms for solo practitioners vs. large firms?

### Contractual:
13. Is our IP license scope appropriate (Section 5.1)?
14. Are our termination provisions balanced?
15. Should we have a separate enterprise agreement template?
16. Do we need customer reference clauses?

---

## Recommended Changes Format

For each document, please provide:

1. **Critical Issues**: Must fix before launch
2. **High Priority**: Should fix before beta
3. **Medium Priority**: Should fix before public launch
4. **Best Practices**: Nice to have improvements

Please mark up the actual page files with:
- `[CRITICAL]` - Legal risk, must address
- `[REVISE]` - Needs rewording for clarity/accuracy
- `[ADD]` - Missing provision that should be added
- `[QUESTION]` - Needs client decision/clarification

---

## Technical Context for Lawyer

### How the Platform Works:

1. **Document Upload**: Law firms upload PDFs, DOCX, emails to matters (cases)
2. **AI Processing**:
   - Text extraction from documents
   - Semantic chunking (breaks into searchable segments)
   - Embedding generation via OpenAI API (vector representations)
   - Storage in PostgreSQL with vector search
3. **Search**: Users search by meaning, not just keywords
4. **Chat**: Users ask questions, AI retrieves relevant chunks and generates answers via Claude API
5. **Multi-Tenancy**: Complete data isolation between law firms (row-level security)

### Third-Party Services We Use:
- **OpenAI**: Text embeddings (search functionality)
- **Anthropic**: Claude 3.5 Sonnet (chat responses)
- **AWS**: Infrastructure (S3, RDS, CloudFront)
- **Sentry**: Error monitoring (configured for privacy)

### Data Flow:
```
User uploads document →
Stored in S3 (encrypted) →
Metadata in PostgreSQL →
Text extracted →
Sent to OpenAI for embeddings →
Embeddings stored in PostgreSQL →
When user searches/chats →
Relevant chunks sent to Claude →
Response with citations returned
```

**Key Point**: We do NOT use client data to train AI models (opt-out enforced with vendors).

---

## Next Steps After Review

1. **Incorporate Feedback**: Update all three legal documents based on lawyer's recommendations
2. **Create DPA**: Draft Data Processing Agreement for enterprise clients
3. **Create Addenda**: If needed, create law-firm-specific addenda
4. **Version Control**: Maintain dated versions of all legal documents
5. **User Notification**: Plan for notifying users of any material changes

---

## Contact Information

For questions during review:
- **Email**: legal@bclegaltech.ca
- **Technical Questions**: Available for clarification calls

**Timeline**: Please provide initial feedback within [X days] if possible, as we're preparing for beta launch.

---

**Thank you for your review. Your expertise is critical to ensuring we meet our legal and ethical obligations to the BC legal community.**
