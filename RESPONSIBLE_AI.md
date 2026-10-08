# GovGuide AI — Responsible AI Framework & Governance

> **Module**: IT3041 – Information Retrieval and Web Analytics (SLIIT)  
> **Document**: RESPONSIBLE_AI.md  
> **System**: GovGuide AI Platform  

---

## 1. Responsible AI Principles for Public Service Delivery

Government information retrieval carries legal, financial, and regulatory consequences for citizens and business owners. Erroneous guidance regarding license categories, fee amounts, or application deadlines can lead to fines, application rejections, or business closures.

GovGuide AI is built on seven non-negotiable **Responsible AI Pillars**:

```
 ┌─────────────────────────────────────────────────────────────┐
 │                  RESPONSIBLE AI PILLARS                     │
 ├─────────────────────────────────────────────────────────────┤
 │ 1. Transparency     ── Clear disclosure of AI generation    │
 │ 2. Explainability   ── Verifiable source chunk citations   │
 │ 3. Grounding        ── Zero extrapolation beyond DB records │
 │ 4. Anti-Hallucination ── Safe refusal when evidence is low  │
 │ 5. Privacy          ── Zero PII logging / data protection   │
 │ 6. Fairness         ── Impartial, non-discriminatory access │
 │ 7. Human Oversight  ── Explicit referrals to official offices│
 └─────────────────────────────────────────────────────────────┘
```

---

## 2. Pillar Implementations in GovGuide AI

### 2.1. Transparency
- **AI Indicator**: Every response presented on the UI is labeled as AI-generated with an explanation badge.
- **Model / System Mode Disclosure**: The system clearly distinguishes between live LLM inference and grounded evidence synthesis mode (`is_demo` flag).
- **Processing Explanations**: The system provides a plain-language summary of how the answer was derived from municipal records.

### 2.2. Explainability & Source Attribution
- **Bracket Citations**: Every factual statement generated in the answer cites its evidentiary origin using `[Source N]` bracket notation.
- **Source Metadata Cards**: The UI displays expandable source cards listing:
  - Official Document Title (e.g. *Retail Food Establishment License*)
  - Municipal Service Code (e.g. *Code 1006*)
  - Specific Document Section (e.g. *fee_schedule*, *required_documents*)
  - Direct Official URL (e.g. `https://www.chicago.gov/BusinessDirect`)
  - Verifiable chunk excerpt.

### 2.3. Evidence Grounding & Zero Fabrication
- **System Invariant**: The system is forbidden from assuming or inventing:
  - Department names or contact details
  - Fee structures and tiers
  - Application forms and paperwork
  - Expiration deadlines or grace periods
- **Evidence Containment**: All retrieved information is encapsulated in `<OFFICIAL_EVIDENCE>` XML tags and treated strictly as passive data.

### 2.4. Hallucination Mitigation & Safe Refusal
- **Threshold Gating**: If the retrieval engine returns a confidence score $< 0.15$ or $0$ relevant records, the system triggers the **Insufficient Evidence Refusal Protocol**:
  > *"I could not find sufficient verified information in the available government sources to answer your specific inquiry. To ensure accuracy, please consult the City of Chicago Department of Business Affairs and Consumer Protection (BACP) directly."*
- **URL Whitelist Validation**: Post-generation checks verify that all referenced URLs point to verified government domains (`chicago.gov`). Any ungrounded link triggers a confidence penalty and removal.

### 2.5. Privacy & Data Minimization
- **No PII Persistence**: Citizen queries are processed in memory; no personal identifying information (names, SSNs, credit card numbers) is logged or stored in conversation history.
- **Session Anonymization**: Sessions are tracked via pseudonymous UUIDs.

### 2.6. Fairness & Impartiality
- **Equitable Access**: Standardized algorithmic search guarantees identical search results for equivalent queries regardless of user background.
- **Plain Language Adaptation**: Translates complex municipal ordinances into accessible citizen-friendly bullet points without altering legal meaning.

### 2.7. Human Oversight & Administrative Referral
Every AI response includes a persistent municipal caveat:
> *"Always verify official requirements, fees, and zoning rules directly with the City of Chicago Small Business Center (121 N. LaSalle St., Room 800) or via Chicago Business Direct prior to submitting an application."*

---

## 3. Responsible AI Risk & Mitigation Matrix

| Risk Dimension | Specific Hazard | System Mitigation Strategy | Implementation Artifact | Residual Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **Hallucination** | LLM generates obsolete fee amount ($500 instead of $660). | Strict grounding prompt + post-generation grounding checker + regex validation against DB chunks. | `app/responsible_ai/grounding_checker.py`, `AdvisoryAgent` | LLM may slightly rephrase nuances if not fully captured in chunk text. |
| **Misinformation** | User asks for non-existent license category; bot invents rules. | Sufficiency threshold ($0.15$) triggers immediate safe refusal; LLM generation bypassed. | `RetrievalAgent._compute_confidence()`, `ResponseVerificationAgent` | Extremely broad queries may retrieve marginal general records. |
| **Context Hijacking** | Malicious text in user query alters system persona. | Heuristic and regex `PromptInjectionGuard` intercepts and aborts request at gateway. | `app/security/prompt_injection_guard.py` | Emerging novel zero-day prompt injection obfuscation formats. |
| **Stale Municipal Data** | Municipal code changes after dataset ingestion. | Prominent source timestamps and mandatory BACP verification caveats on every answer. | `CaveatCard.jsx`, `ConfidenceBadge.jsx` | Static datasets require periodic re-ingestion pipelines. |
| **Over-reliance** | Citizen treats AI answer as legal advice. | Mandatory legal disclaimers and explicit human office referrals embedded in UI and schema. | `QueryResponse.caveats`, `ChatPage.jsx` | User ignoring warning banners on screen. |
