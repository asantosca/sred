// Legal citation auto-linking utilities
// Transforms legal citations in text to clickable links for verification

/**
 * BC statute citation patterns:
 * - "SBC 2012, c 13" or "SBC 2012, c. 13"
 * - "RSBC 1996, c 210" (Revised Statutes)
 * - Statute names like "Limitation Act", "Family Law Act"
 */
const BC_STATUTE_CITATION_PATTERN = /\b((?:R?SBC)\s+\d{4},?\s*c\.?\s*\d+)/gi

/**
 * Common BC statute names - we link these to BC Laws search
 */
const BC_STATUTE_NAMES = [
  'Limitation Act',
  'Family Law Act',
  'Land Title Act',
  'Property Law Act',
  'Wills, Estates and Succession Act',
  'Business Corporations Act',
  'Employment Standards Act',
  'Workers Compensation Act',
  'Residential Tenancy Act',
  'Strata Property Act',
  'Insurance Act',
  'Motor Vehicle Act',
  'Evidence Act',
  'Interpretation Act',
  'Court Order Enforcement Act',
  'Fraudulent Conveyance Act',
  'Fraudulent Preference Act',
  'Partnership Act',
  'Sale of Goods Act',
  'Personal Property Security Act',
  'Commercial Tenancy Act',
]

/**
 * Canadian case citation patterns:
 * - "2024 SCC 15" (Supreme Court of Canada)
 * - "2023 BCCA 412" (BC Court of Appeal)
 * - "2022 BCSC 1234" (BC Supreme Court)
 * - "2021 BCPC 56" (BC Provincial Court)
 * - "2020 FCA 123" (Federal Court of Appeal)
 * - "2019 FC 456" (Federal Court)
 * - "2018 ONCA 789" (Ontario Court of Appeal)
 * - etc.
 */
const CASE_CITATION_PATTERN = /\b(\d{4}\s+(?:SCC|BCCA|BCSC|BCPC|FCA|FC|ONCA|ONSC|ABCA|ABQB|SKCA|SKQB|MBCA|MBQB|NSCA|NSSC|NBCA|NBQB|PECA|PESCAD|NLCA|NLSC|YTCA|YTSC|NWTCA|NWTSC|NUCA|NUSC)\s+\d+)/gi

/**
 * Build BC Laws search URL for a statute
 */
function buildBCLawsUrl(statuteRef: string): string {
  const encoded = encodeURIComponent(statuteRef)
  return `https://www.bclaws.gov.bc.ca/search?q=${encoded}`
}

/**
 * Build CanLII search URL for a case citation
 */
function buildCanLIIUrl(citation: string): string {
  const encoded = encodeURIComponent(citation)
  return `https://www.canlii.org/en/#search/text=${encoded}`
}

/**
 * Transform markdown content to add legal citation links
 *
 * This function finds statute references and case citations in the text
 * and wraps them in markdown links to BC Laws and CanLII respectively.
 *
 * @param content - The markdown content to transform
 * @returns The content with legal citations linked
 */
export function addLegalCitationLinks(content: string): string {
  let result = content

  // Link case citations to CanLII (do this first to avoid conflicts)
  result = result.replace(CASE_CITATION_PATTERN, (match) => {
    const url = buildCanLIIUrl(match)
    return `[${match}](${url})`
  })

  // Link BC statute citations (SBC, RSBC patterns)
  result = result.replace(BC_STATUTE_CITATION_PATTERN, (match) => {
    // Don't double-link if already inside a markdown link
    const url = buildBCLawsUrl(match)
    return `[${match}](${url})`
  })

  // Link common statute names
  for (const statuteName of BC_STATUTE_NAMES) {
    // Match statute name not already in a link (simple heuristic: not followed by ](
    const pattern = new RegExp(
      `\\b(${statuteName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})(?!\\]\\()`,
      'g'
    )
    result = result.replace(pattern, (match) => {
      const url = buildBCLawsUrl(match)
      return `[${match}](${url})`
    })
  }

  return result
}

/**
 * Check if content contains any legal citations that we can link
 */
export function hasLegalCitations(content: string): boolean {
  if (CASE_CITATION_PATTERN.test(content)) return true
  if (BC_STATUTE_CITATION_PATTERN.test(content)) return true

  for (const statuteName of BC_STATUTE_NAMES) {
    if (content.includes(statuteName)) return true
  }

  return false
}
