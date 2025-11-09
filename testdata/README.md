# Test Data for BC Legal Tech Platform

This directory contains realistic test data for a British Columbia legal document management and AI chat system. The data is designed to test multi-tenancy, document isolation, and AI question-answering capabilities.

## Structure

```
testdata/
├── pacific_legal_llp/                     (Law Firm 1 - Vancouver)
│   ├── matter_1_construction_lien/
│   │   ├── notice_of_civil_claim.txt
│   │   ├── construction_contract.txt
│   │   └── correspondence.txt
│   │
│   └── matter_2_wrongful_dismissal/
│       ├── notice_of_civil_claim.txt
│       ├── employment_offer_letter.txt
│       ├── performance_reviews.txt
│       └── termination_correspondence.txt
│
├── fraser_law_corporation/                (Law Firm 2 - Surrey)
│   ├── matter_1_commercial_lease_dispute/
│   │   ├── notice_of_civil_claim.txt
│   │   ├── commercial_lease.txt
│   │   └── correspondence.txt
│   │
│   └── matter_2_shareholder_dispute/
│       ├── notice_of_civil_claim.txt
│       ├── shareholders_agreement.txt
│       └── email_correspondence.txt
│
├── TEST_QUESTIONS_AND_ANSWERS.md         (Testing script)
└── README.md                              (This file)
```

## Law Firms and Matters

### Pacific Legal LLP (Vancouver)

**Matter 1: Construction Lien - Westcoast Builders Ltd. v. Pacific Ridge Developments Inc.**
- Case Type: Builders Lien Act claim
- Court: BC Supreme Court, Vancouver Registry
- Amount in Dispute: $1,425,000
- Key Issue: Unpaid construction invoices for 42-unit condo development
- Key Documents: Construction contract (CCDC 2), invoices, correspondence, notice of civil claim

**Matter 2: Wrongful Dismissal - Patricia Wong v. MetroTech Solutions Inc.**
- Case Type: Employment law / wrongful dismissal
- Court: BC Supreme Court, Vancouver Registry
- Key Issue: Inadequate notice period (2 weeks vs. 12 months claimed)
- Employee Profile: 47 years old, Director level, 5.4 years service, excellent performance
- Key Documents: Employment offer, performance reviews, termination letter, correspondence

### Fraser Law Corporation (Surrey)

**Matter 1: Commercial Lease Dispute - Riverside Restaurant Group Ltd. v. Delta Commercial Properties Inc.**
- Case Type: Commercial lease / contract dispute
- Court: BC Supreme Court, New Westminster Registry
- Key Issue: Landlord refusing to honour lease renewal option
- Amount at Stake: $500,000 (leasehold improvements, goodwill, relocation)
- Key Documents: Commercial lease with renewal option, correspondence, notice of civil claim

**Matter 2: Shareholder Dispute - David Kumar v. Innovate Tech Solutions Inc. et al.**
- Case Type: Shareholder oppression (Business Corporations Act, s. 227)
- Court: BC Supreme Court, New Westminster Registry
- Key Issue: Minority shareholder (33.33%) being oppressed by majority
- Oppressive Conduct: Exclusion from information, dividend suppression, business diversion
- Key Documents: Unanimous shareholders agreement, corporate records, email correspondence

## Testing Scenarios

### Multi-Tenancy Tests
- Verify that lawyers at Pacific Legal can only access Pacific Legal matters
- Verify that lawyers at Fraser Law can only access Fraser Law matters
- Test cross-firm query isolation

### Document Search and Retrieval
- Search by dollar amounts, dates, party names
- Search for specific legal provisions (e.g., "Builders Lien Act")
- Search across multiple documents in a matter

### AI Question Answering
- See `TEST_QUESTIONS_AND_ANSWERS.md` for 25 test questions covering:
  - Factual questions about each matter
  - Legal analysis questions
  - Multi-document synthesis
  - Multi-tenancy isolation tests

### Citation Testing
- Verify AI cites specific documents and sections
- Test source attribution accuracy
- Verify links to original documents work correctly

## Key Features to Test

1. **BC Legal Context**
   - References to BC legislation (Builders Lien Act, Employment Standards Act, Business Corporations Act, etc.)
   - BC courts (BC Supreme Court, specific registries)
   - BC locations (Vancouver, Surrey, Burnaby, New Westminster)
   - Canadian corporate structures (Ltd., Inc., LLP)

2. **Realistic Legal Documents**
   - Proper court document formatting
   - Authentic legal correspondence patterns
   - Realistic timelines and dollar amounts
   - Common legal issues BC lawyers encounter

3. **Complex Matter Scenarios**
   - Multiple documents per matter
   - Chronological correspondence trails
   - Conflicting claims requiring document analysis
   - Issues requiring cross-referencing multiple documents

4. **Document Variety**
   - Court pleadings (Notices of Civil Claim, Petitions)
   - Contracts (Construction, Employment, Commercial Lease, Shareholders Agreement)
   - Correspondence (emails, demand letters, lawyer communications)
   - Corporate documents (performance reviews, minutes, financial information)

## How to Use This Test Data

### Option 1: Manual Upload
1. Create two test user accounts (one for each law firm)
2. Create matters in each account matching the folder structure
3. Upload documents to corresponding matters
4. Test queries using the questions in TEST_QUESTIONS_AND_ANSWERS.md

### Option 2: Automated Seed Script
Create a script to:
1. Create test organizations for each law firm
2. Create test users for each organization
3. Create matters with proper metadata
4. Upload and process documents
5. Run automated tests against the test questions

### Option 3: Database Seed
1. Create database seed script that directly inserts:
   - Organizations (law firms)
   - Users
   - Matters
   - Documents with pre-processed text
2. Useful for rapid testing and CI/CD

## Expected Behavior

When a lawyer asks: "How much is owed to Westcoast Builders?"

**Correct Response:**
"Based on the Notice of Civil Claim and correspondence in the Westcoast Builders v. Pacific Ridge matter, the total outstanding amount is $1,425,000:
- Invoice #8 (Sept 1, 2023): $875,000
- Invoice #9 (Oct 1, 2023): $550,000

Payment was due under the Builders Lien Act within 17 days of invoice. A Claim of Lien was filed October 20, 2023."

**With source citations:**
[Construction Contract, Section A-3.2]
[Correspondence, Email dated Sept 18, 2023]
[Notice of Civil Claim, Paragraph 10]

## Notes

- All names, addresses, and companies are fictional
- Dollar amounts and dates are realistic but invented
- Legal issues are based on common BC legal matters
- Documents follow authentic BC legal practice standards
- Designed to be comprehensive but manageable for testing

## Maintenance

To add new test matters:
1. Create new folder under appropriate law firm
2. Add realistic documents covering the matter
3. Add test questions to TEST_QUESTIONS_AND_ANSWERS.md
4. Update this README

---

Last Updated: 2023-11-09
Version: 1.0
