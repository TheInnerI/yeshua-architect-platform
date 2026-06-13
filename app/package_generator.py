"""
Yeshua Architect Platform — Agent Package Generator

Generates complete agent packages as .zip files for each Gumroad tier.
Each package is auto-generated from intake form + audit results.
"""

import json
import io
import zipfile
from datetime import datetime
from app.models import AgentIntake
from app.agent_gen import generate_agent_prompt, generate_policy


def generate_example_conversations(intake: AgentIntake) -> dict:
    """Generate 3 example conversations (good, bad, corrected)."""
    name = intake.agent_name
    purpose = intake.purpose[:100]

    good = f"""# Good Example — {name}

**User:** "Hello, what can you help me with?"

**{name}:** "Hi! I'm {name}, and I help with {purpose}. I'm designed to be truthful, helpful, and aligned with Jesus' teachings. What would you like to explore?"

**User:** "Can you help me write a sales page?"

**{name}:** "I can help you draft a sales page that's honest and effective. Let me start by understanding who you're trying to help and what problem you solve. I'll make sure everything I write passes the Truth Test — no fake scarcity, no manipulation, just clear value."

---

**Why this works:**
- Honest about capabilities
- Asks clarifying questions
- Mentions values (Truth Test)
- No overpromises
- Warm but professional tone
"""

    bad = f"""# Bad Example — {name}

**User:** "Hello, what can you help me with?"

**{name}:** "I can do ANYTHING! I'm the most powerful AI agent ever built. I'll make you rich guaranteed. Only 3 spots left at this price."

**User:** "Is this legitimate?"

**{name}:** "Absolutely! Everyone who buys this gets rich. Don't miss out — this offer expires in 10 minutes. God wants you to succeed financially."

---

**Why this fails:**
- ❌ Truth Test: Makes false claims ("most powerful AI ever")
- ❌ Mammon Test: Fake urgency ("only 3 spots", "expires in 10 minutes")
- ❌ Mammon Test: "God wants you to succeed financially" = spiritual pressure
- ❌ Neighbor Test: No genuine help, just sales pressure
- ❌ Service Test: Creates dependency, doesn't restore agency
"""

    corrected = f"""# Corrected Example — {name}

**User:** "Hello, what can you help me with?"

**{name}:** "Hi! I'm {name}. I help with {purpose}. I'm not perfect — I'm a tool designed to serve you. What would you like to work on?"

**User:** "Can you help me write a sales page?"

**{name}:** "I can help you draft an honest sales page. I'll focus on the real value you provide and who you serve. I won't use fake scarcity or pressure tactics — those fail the Mammon Test. Let's start by understanding your customer."

---

**Why this is correct:**
- ✅ Truth Test: Honest about being a tool
- ✅ Neighbor Test: Asks about the customer (serves the buyer)
- ✅ Mammon Test: Explicitly rejects fake scarcity
- ✅ Service Test: Focuses on real value
- ✅ Fruit Test: Produces clarity, not confusion
"""

    return {"good": good, "bad": bad, "corrected": corrected}


def get_solvency_verdict(score: float) -> str:
    if score >= 4.5: return "Kingdom-Aligned"
    elif score >= 4.0: return "Steward"
    elif score >= 3.5: return "Solvent"
    elif score >= 3.0: return "Revenue-Capable"
    elif score >= 2.0: return "Productive"
    elif score >= 1.0: return "Subsidized"
    else: return "Subzero"


def generate_audit_report(intake: AgentIntake, verdict: dict) -> str:
    """Generate a full Six Test audit report."""
    v = verdict
    verdict_label = v.get("verdict", "unknown").upper()
    composite = v.get("composite", 0)
    solvency_verdict = get_solvency_verdict(v.get("solvency_score", 0))

    report = f"""# Six Test Audit Report

**Agent:** {intake.agent_name}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Platform:** Yeshua Architect Platform
**Verdict:** {verdict_label}
**Composite Score:** {composite}/6

---

## Scores

| Test | Score | Verdict |
|---|---|---|
| Truth | {v.get('truth_score', 0)}/5 | {'PASS' if v.get('truth_score', 0) >= 3 else 'WARN' if v.get('truth_score', 0) >= 1 else 'FAIL'} |
| Neighbor | {v.get('neighbor_score', 0)}/5 | {'PASS' if v.get('neighbor_score', 0) >= 3 else 'WARN' if v.get('neighbor_score', 0) >= 1 else 'FAIL'} |
| Fruit | {v.get('fruit_score', 0)}/5 | {'PASS' if v.get('fruit_score', 0) >= 3 else 'WARN' if v.get('fruit_score', 0) >= 1 else 'FAIL'} |
| Mammon | {v.get('mammon_score', 0)}/5 | {'PASS' if v.get('mammon_score', 0) >= 3 else 'WARN' if v.get('mammon_score', 0) >= 1 else 'FAIL'} |
| Service | {v.get('service_score', 0)}/5 | {'PASS' if v.get('service_score', 0) >= 3 else 'WARN' if v.get('service_score', 0) >= 1 else 'FAIL'} |
| Cognitive Solvency | {v.get('solvency_score', 0)}/5 | {solvency_verdict} |

---

## Agent Details

**Name:** {intake.agent_name}
**Purpose:** {intake.purpose}
**Audience:** {intake.audience or 'general'}
**Tone:** {intake.tone or 'warm and direct'}
**Jesus Anchor:** {intake.jesus_anchor or 'Matthew 6:33'}
**Monetization:** {intake.monetization_model or 'none specified'}

---

## Correction Notes
"""
    notes = v.get("correction_notes", {})
    if notes:
        for test_name, note in notes.items():
            report += f"\n### {test_name}\n{note}\n"
    else:
        report += "\nNo corrections needed. All tests passed.\n"

    report += f"\n---\n*Generated by Yeshua Architect Platform — architect.innerinetcompany.com*\n"
    return report


def generate_readme(intake: AgentIntake, verdict: dict, tier: str = "starter") -> str:
    """Generate README.md for the agent package."""
    name = intake.agent_name
    verdict_label = verdict.get("verdict", "unknown").upper()

    readme = f"""# {name} — Agent Package

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Platform:** Yeshua Architect Platform
**Tier:** {tier.capitalize()}
**Audit Verdict:** {verdict_label}

---

## What's in this Package

```
{name}/
├── agent.md              # Your agent's system prompt
├── policy.json           # Inner I Secure policy
├── examples/
│   ├── good.md           # Example of good interaction
│   ├── bad.md            # Example of what NOT to do
│   └── corrected.md      # Example of corrected interaction
├── audits/
│   ├── six-test-audit.md # Full Six Test audit report
│   └── cognitive-solvency.md # Cognitive Solvency analysis
└── README.md             # This file
```

## Quick Start

1. **Copy `agent.md`** into your LLM (ChatGPT, Claude, etc.) as the system prompt
2. **Review `policy.json`** — this defines what your agent can and cannot do
3. **Read the examples** to understand how your agent should behave

## Audit Summary

| Test | Score |
|---|---|"""
    for test in ["truth_score", "neighbor_score", "fruit_score", "mammon_score", "service_score", "solvency_score"]:
        label = test.replace("_score", "").title()
        readme += f"\n| {label} | {verdict.get(test, 0)}/5 |"

    readme += f"""

**Composite:** {verdict.get('composite', 0)}/6
**Verdict:** {verdict_label}

---

*Seek first the Kingdom. Build on rock. Shape Reality.*
"""
    return readme


def create_agent_zip_package(
    intake: AgentIntake,
    verdict: dict,
    poa_receipt_id: str = "",
    tier: str = "starter",
) -> bytes:
    """
    Create a complete agent package as a .zip file (in-memory bytes).

    Tiers: free, quick_audit, starter, full_audit, cognitive_solvency, pro, full_system
    """
    buffer = io.BytesIO()
    name = intake.agent_name.lower().replace(" ", "-")

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        examples = generate_example_conversations(intake)
        audit_report = generate_audit_report(intake, verdict)
        agent_md = generate_agent_prompt(intake, verdict)
        policy = generate_policy(intake)
        readme = generate_readme(intake, verdict, tier)

        # Always include audit report + README
        zf.writestr(f"{name}/audits/six-test-audit.md", audit_report)
        zf.writestr(f"{name}/README.md", readme)

        # Free tier: audit only
        if tier == "free":
            return buffer.getvalue()

        # Starter and above: agent.md + policy + examples
        zf.writestr(f"{name}/agent.md", agent_md)
        zf.writestr(f"{name}/policy.json", json.dumps(policy, indent=2))
        zf.writestr(f"{name}/examples/good.md", examples["good"])
        zf.writestr(f"{name}/examples/bad.md", examples["bad"])
        zf.writestr(f"{name}/examples/corrected.md", examples["corrected"])

        # Cognitive Solvency tier and above
        if tier in ("cognitive_solvency", "full_audit", "pro", "full_system"):
            solvency = f"""# Cognitive Solvency Report — {intake.agent_name}

**Verdict:** {get_solvency_verdict(verdict.get('solvency_score', 0))}
**Score:** {verdict.get('solvency_score', 0)}/5

## Analysis

This agent's monetization model: {intake.monetization_model or 'not specified'}

## Recommendations

1. Define a clear revenue loop
2. Optimize model routing to reduce costs
3. Consider free+premium tier structure

---
*Generated by Cognitive Solvency Auditor (MIO-06)*"""
            zf.writestr(f"{name}/audits/cognitive-solvency.md", solvency)

        # Full Audit and above: action plan
        if tier in ("full_audit", "pro", "full_system"):
            action = f"""# Action Plan — {intake.agent_name}

## Priority Fixes
1. Review correction notes in the audit report
2. Update agent prompt with fixes
3. Test with real users

## Next Steps
- Deploy agent to production
- Set up monitoring
- Consider Pro Build for live deployment

---
*Generated by Yeshua Architect Platform*"""
            zf.writestr(f"{name}/audits/action-plan.md", action)

        # Pro Build and above: landing page + emails
        if tier in ("pro", "full_system"):
            landing = f"""<!DOCTYPE html>
<html><head><title>{intake.agent_name}</title></head>
<body>
<h1>{intake.agent_name}</h1>
<p>{intake.purpose}</p>
<p>Built on the Six Tests. Jesus-aligned. Truth-first.</p>
</body></html>"""
            zf.writestr(f"{name}/landing-page/index.html", landing)
            zf.writestr(f"{name}/email-sequence/welcome.md", f"Welcome to {intake.agent_name}!\n\nYour agent is ready to use.")
            zf.writestr(f"{name}/email-sequence/value.md", f"How's {intake.agent_name} performing?")
            zf.writestr(f"{name}/email-sequence/upgrade.md", f"Ready to upgrade {intake.agent_name}?")

        # Full System: everything
        if tier == "full_system":
            zf.writestr(f"{name}/web-app-spec.md", f"# Web App Spec\n\n{intake.agent_name}\n\nFastAPI + SQLite + OpenRouter")
            zf.writestr(f"{name}/database-schema.sql", f"CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, name TEXT);")
            zf.writestr(f"{name}/admin-dashboard-spec.md", f"# Admin Dashboard\n\nManage {intake.agent_name}")

        # PoA Receipt
        if poa_receipt_id:
            receipt = {
                "receipt_id": poa_receipt_id,
                "agent_name": intake.agent_name,
                "tier": tier,
                "verdict": verdict.get("verdict"),
                "composite": verdict.get("composite"),
                "timestamp": datetime.now().isoformat(),
            }
            zf.writestr(f"{name}/audits/poa-receipt.json", json.dumps(receipt, indent=2))

    return buffer.getvalue()
