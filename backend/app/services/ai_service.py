"""
AI analysis service using Google Gemini (gemini-2.0-flash).
Provides streaming site analysis, site comparison, and natural language Q&A.
"""
from typing import Generator
from google import genai
from app.models.schemas import SiteReadinessScore

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are GeoSite AI, an expert commercial real estate and infrastructure site analyst with 20+ years of experience. You specialize in location intelligence, geospatial analysis, and site selection for retail, logistics, energy, and telecom projects.

Your analysis style:
- Data-driven: Always reference specific numbers from the scoring data
- Actionable: Give concrete next steps, not vague advice
- Expert: Draw on real industry knowledge beyond just the scores
- Honest: Acknowledge trade-offs and risks clearly

Format your responses with clear ## headers and bullet points for readability."""


def get_client(api_key: str) -> genai.Client:
    if not api_key:
        raise RuntimeError("Gemini API key not provided.")
    return genai.Client(api_key=api_key)


def _format_breakdown(site: SiteReadinessScore) -> str:
    lines = []
    for b in site.breakdowns:
        factor_str = ", ".join(
            f"{k.replace('_', ' ')}: {v}"
            for k, v in list(b.factors.items())[:5]
        )
        lines.append(
            f"• **{b.layer_name.replace('_', ' ').title()}**: {b.score:.1f}/100 "
            f"(weight {b.weight:.0%}, contributes {b.contribution:.1f} pts)\n"
            f"  Data → {factor_str}"
        )
    return "\n".join(lines)


def stream_site_analysis(site: SiteReadinessScore, use_case: str, api_key: str = "") -> Generator[str, None, None]:
    """Stream deep AI analysis of a scored site."""
    client = get_client(api_key)
    breakdown = _format_breakdown(site)

    prompt = f"""{SYSTEM_PROMPT}

Analyze this site readiness report for a **{use_case.replace('_', ' ').title()}** deployment:

**Location:** {site.lat:.4f}°N, {site.lng:.4f}°W
**Composite Score:** {site.composite_score}/100 (Grade: **{site.grade}**)
**H3 Cell:** `{site.h3_index}`

**Layer-by-Layer Breakdown:**
{breakdown}

Provide a comprehensive expert analysis with these sections:

## Executive Summary
Is {site.composite_score}/100 exceptional, typical, or concerning for a {use_case.replace('_', ' ')} site?

## Key Strengths
What makes this location specifically advantageous? Reference exact numbers.

## Critical Risks
What are the real concerns based on the data? Be direct.

## Hidden Insights
What non-obvious conclusions can you draw from the data patterns?

## Market Intelligence
Based on the POI and competitor scores, what does the competitive landscape look like?

## Required Due Diligence
List 3-5 specific next steps before committing to this site.

## Final Verdict
**Go / No-Go / Conditional Go** — with 2-3 sentence reasoning."""

    for chunk in client.models.generate_content_stream(model=MODEL, contents=prompt):
        if chunk.text:
            yield chunk.text


def stream_site_comparison(sites: list[SiteReadinessScore], use_case: str, api_key: str = "") -> Generator[str, None, None]:
    """Stream AI comparison and ranking of multiple candidate sites."""
    client = get_client(api_key)

    sites_text = "\n\n".join([
        f"**Site {i+1}** — ({s.lat:.4f}°N, {s.lng:.4f}°W) | Score: {s.composite_score:.1f}/100 (Grade {s.grade})\n" +
        "\n".join([
            f"  • {b.layer_name.replace('_', ' ').title()}: {b.score:.1f}/100 ({b.weight:.0%} weight)"
            for b in s.breakdowns
        ])
        for i, s in enumerate(sites)
    ])

    prompt = f"""{SYSTEM_PROMPT}

Compare these {len(sites)} candidate sites for a **{use_case.replace('_', ' ').title()}** deployment:

{sites_text}

Provide:

## Winner Declaration
Which site wins? State it directly in the first sentence.

## Head-to-Head Analysis
Compare each dimension across all sites.

## Hidden Trade-offs
Non-obvious trade-offs the scores alone don't capture.

## Risk-Adjusted Ranking
Rank all {len(sites)} sites accounting for downside risk.

## Action Plan
Concrete next steps for the team."""

    for chunk in client.models.generate_content_stream(model=MODEL, contents=prompt):
        if chunk.text:
            yield chunk.text


def stream_site_query(question: str, site: SiteReadinessScore, use_case: str, api_key: str = "") -> Generator[str, None, None]:
    """Stream answer to a natural language question about a site."""
    client = get_client(api_key)

    context = (
        f"Site: ({site.lat:.4f}°N, {site.lng:.4f}°W) | "
        f"Use case: {use_case} | Score: {site.composite_score}/100 (Grade {site.grade})\n"
        "Layers: " + ", ".join(f"{b.layer_name}={b.score:.0f}" for b in site.breakdowns) + "\n"
        "Key factors: " + " | ".join(
            f"{b.layer_name}: " + ", ".join(f"{k}={v}" for k, v in list(b.factors.items())[:3])
            for b in site.breakdowns
        )
    )

    prompt = f"""{SYSTEM_PROMPT}

Site data context:
{context}

User question: {question}

Answer as an expert location intelligence analyst. Be specific and reference the actual data."""

    for chunk in client.models.generate_content_stream(model=MODEL, contents=prompt):
        if chunk.text:
            yield chunk.text
