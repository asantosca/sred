# SR&ED Domain Guide

This document provides essential SR&ED (Scientific Research and Experimental Development) terminology and concepts for developers working on the platform.

## What is SR&ED?

SR&ED is a Canadian federal tax incentive program that encourages businesses to conduct research and development in Canada. It provides:

- **Investment Tax Credits (ITCs)** - Direct reduction in taxes owed
- **Refundable credits** - Cash refunds for qualifying Canadian-controlled private corporations (CCPCs)

The program is administered by the **Canada Revenue Agency (CRA)**.

## The Five-Question Test

The CRA uses a five-question test to determine SR&ED eligibility. Our AI should evaluate projects against these criteria:

### 1. Technological Uncertainty

**Question**: Was there a technological uncertainty that could not be resolved through routine engineering or standard practice?

**What to look for**:
- Unknown outcomes or approaches
- Problems that required experimentation
- Gaps in available knowledge
- Failures or unexpected results

**Red flags** (NOT eligible):
- Well-documented solutions existed
- Standard industry practice was followed
- Only business or design uncertainty (not technical)

### 2. Systematic Investigation

**Question**: Did the work involve a systematic investigation or search using scientific or technological principles?

**What to look for**:
- Hypothesis formation
- Planned experiments or tests
- Data collection and analysis
- Iterative refinement
- Documentation of methodology

**Red flags** (NOT eligible):
- Trial and error without analysis
- No documented methodology
- Random attempts without learning

### 3. Technological Advancement

**Question**: Was the work undertaken for the purpose of achieving a technological advancement?

**What to look for**:
- New knowledge or capabilities
- Improved understanding of technology
- Novel solutions to technical problems
- Advances beyond current practice

**Red flags** (NOT eligible):
- Only business improvements (cost, speed)
- Cosmetic or aesthetic changes
- Market research or user studies

### 4. Scientific/Technical Content

**Question**: Did the work have scientific or technological content?

**What to look for**:
- Qualified personnel (engineers, scientists)
- Technical skills applied
- Scientific/engineering principles used

### 5. Documentation

**Question**: Is there contemporaneous documentation?

**What to look for**:
- Project plans and specifications
- Test results and analysis
- Meeting notes and emails
- Lab notebooks
- Progress reports

## T661 Form Structure

The **T661** is the CRA form used to claim SR&ED tax credits. Key sections:

### Part 2: Project Information
- Project title
- Field of science/technology
- Start and end dates
- Business number

### Part 3: Scientific or Technological Objectives
- What technological advancement was sought?
- What was the project trying to achieve technically?

**Writing tips**:
- Be specific about technical goals
- Distinguish from business objectives
- Use measurable outcomes where possible

### Part 4: Technological Uncertainties
- What was unknown at the start?
- Why couldn't this be resolved through routine engineering?

**Writing tips**:
- Describe what was uncertain, not what was unknown to the claimant
- Explain why existing knowledge was insufficient
- Reference the state of technology at project start

### Part 5: Work Done
- What systematic investigation was undertaken?
- What hypotheses were formed and tested?
- How were results analyzed?

**Writing tips**:
- Describe the methodology
- Show the iterative process
- Explain how failures informed progress

### Part 6: Conclusions
- What was achieved or learned?
- Were the uncertainties resolved?
- What advancement resulted?

**Writing tips**:
- Summarize technical outcomes
- Connect results to objectives
- Note any remaining uncertainties

## Eligible Expenditures

### Salaries and Wages
- Time spent directly on SR&ED activities
- Must be for employees (not contractors)
- Includes taxable benefits
- Requires time tracking documentation

### Materials
- Consumed or transformed in SR&ED
- Must be used directly in experiments
- NOT capital equipment (can be depreciated separately)

### Contractors/Subcontractors
- Third-party R&D work
- Must be for SR&ED activities
- Contract should specify work performed

### Overhead
Two methods:
1. **Proxy Method**: 55% of eligible salaries (simplified)
2. **Traditional Method**: Actual overhead allocation (more complex)

## Document Categories

For document classification in the platform:

| Category | Description | SR&ED Relevance |
|----------|-------------|-----------------|
| `project_plan` | Technical specifications, proposals | Objectives, methodology |
| `timesheet` | Labor hour records | Salary expenditure support |
| `email` | Project communications | Contemporaneous documentation |
| `financial` | Budgets, expenses | Expenditure support |
| `technical_report` | Test results, analysis | Work done, advancement |
| `lab_notebook` | Experiment logs | Systematic investigation |
| `invoice` | Contractor bills | Third-party costs |

## Common Terminology

| Term | Definition |
|------|------------|
| **ITC** | Investment Tax Credit - the credit claimed |
| **CCPC** | Canadian-Controlled Private Corporation - gets enhanced rates |
| **Proxy method** | Simplified overhead calculation (55% of salaries) |
| **Contemporaneous** | Documentation created at the time of work |
| **Technological advancement** | New knowledge or capability gained |
| **Routine engineering** | Standard practice that doesn't qualify |
| **Fiscal year end** | The company's year-end date for tax purposes |
| **NAICS code** | Industry classification code |
| **CRA** | Canada Revenue Agency |
| **T661** | The SR&ED claim form |

## AI Prompt Guidelines

When generating SR&ED content, the AI should:

### DO:
- Always cite document sources
- Use the five-question framework
- Distinguish between document evidence and general knowledge
- Flag areas needing more documentation
- Use technical language appropriate to the field
- Qualify uncertain conclusions

### DON'T:
- Invent specific CRA policy references
- Make definitive eligibility determinations
- Ignore gaps in evidence
- Use business-only justifications
- Overstate technological advancement

### Key Phrases to Use:
- "Based on [Source X], the project faced uncertainty in..."
- "The documentation suggests systematic investigation through..."
- "Evidence of technological advancement includes..."
- "This area may require additional documentation..."
- "Generally for SR&ED claims... (verify with current CRA guidance)"

## Resources

- [CRA SR&ED Program](https://www.canada.ca/en/revenue-agency/services/scientific-research-experimental-development-tax-incentive-program.html)
- [T661 Form and Guide](https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/t661.html)
- [SR&ED Eligibility Policy](https://www.canada.ca/en/revenue-agency/services/scientific-research-experimental-development-tax-incentive-program/policies-procedures-guidelines/eligibility-work-sred-tax-incentives-policy.html)
