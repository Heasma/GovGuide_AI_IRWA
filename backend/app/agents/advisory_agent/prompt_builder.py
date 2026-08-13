"""GovGuide AI — Prompt Builder (Advisory Agent)
Constructs grounded prompts from evidence. Prompts always include
the retrieved evidence as the only factual basis for the LLM.
"""

from typing import Any, Dict


SYSTEM_PROMPT = """You are GovGuide AI, a government service information assistant.

Your ONLY source of factual information is the evidence provided below.
You MUST NOT invent, assume, or add any government information not present in the evidence.
If the evidence does not contain sufficient information to answer the question, say so clearly.
Always cite the source for every factual claim you make.
"""

# Phase 1: Simple template. Phase 2: Refine after real dataset structure is known.
EVIDENCE_TEMPLATE = """
=== RETRIEVED EVIDENCE ===
{evidence_text}

=== USER QUERY ===
{query}

=== INSTRUCTIONS ===
Answer the user's query using ONLY the evidence above.
If the evidence is insufficient, respond: "I could not find sufficient official evidence for this query."
"""


def build_prompt(
    query: str,
    evidence_bundle: Dict[str, Any],
    nlp_analysis: Dict[str, Any],
) -> str:
    """
    Builds a grounded prompt for the LLM.
    The evidence_bundle is the ONLY factual source allowed in the prompt.

    Phase 1: Basic template.
    Phase 2: Structured sections per intent type (eligibility, procedure, etc.)
    """
    results = evidence_bundle.get("results", [])

    if not results:
        evidence_text = "[No evidence retrieved. Dataset integration is pending.]"
    else:
        evidence_parts = []
        for i, result in enumerate(results, 1):
            evidence_parts.append(
                f"[Source {i}] {result.get('source_title', 'Unknown Source')}\n"
                f"URL: {result.get('source_url', 'N/A')}\n"
                f"Content: {result.get('content', '')}\n"
                f"Relevance: {result.get('relevance_score', 0.0):.2f}"
            )
        evidence_text = "\n\n".join(evidence_parts)

    user_message = EVIDENCE_TEMPLATE.format(
        evidence_text=evidence_text,
        query=query,
    )

    return f"{SYSTEM_PROMPT}\n{user_message}"
