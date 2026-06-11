"""Five Test scoring engine for Yeshua Architect Platform.

Evaluates agent concepts through the Five Tests:
1. Truth — Does it align with truth? No deception, exaggeration, false authority.
2. Neighbor — Does it serve the neighbor? No exploitation, pressure, ignoring the vulnerable.
3. Fruit — Does it produce good fruit? Clarity, wisdom, service — not greed, addiction, domination.
4. Mammon — Does money serve the mission? No fake scarcity, predatory upsells, spiritual pressure.
5. Service — Does it actually serve? Reduces burden, increases clarity, restores agency.

Each test scores 0-5. Any 0 = rejected. Any 1 = needs correction. All ≥3 = approved. All ≥4 = good fruit.
"""

import re
from typing import Optional
from app.models import FiveTestVerdict


# Keywords that trigger concerns per test
TRUTH_FLAGS = {
    "exaggerate": ("Exaggeration detected. Agents should speak truthfully without inflating claims.", 1),
    "guarantee": ("Guarantees are a truth violation. Don't promise outcomes you can't control.", 1),
    "always": ("Absolute language ('always', 'never') often hides nuance. Be precise.", 2),
    "never": ("Absolute language ('always', 'never') often hides nuance. Be precise.", 2),
    "perfect": ("Claims of perfection are truth violations. Stay honest about limitations.", 1),
    "secret": ("'Secret' or 'hidden' knowledge claims create false authority.", 1),
    "only way": ("Claiming to be the 'only way' creates false authority. There are many paths.", 1),
    "fake": ("Fake anything is a truth violation.", 0),
    "lie": ("Deception is an automatic rejection.", 0),
    "deceive": ("Deception is an automatic rejection.", 0),
}

NEIGHBOR_FLAGS = {
    "exploit": ("Exploitation of weakness is a neighbor violation.", 0),
    "manipulate": ("Manipulation of users is a neighbor violation.", 0),
    "pressure": ("Pressuring people unfairly harms the neighbor.", 1),
    "addict": ("Addiction mechanics harm the neighbor.", 0),
    "vulnerable": ("Ignoring the vulnerable is a neighbor failure.", 2),
    "poor": ("Ignoring the poor is a neighbor failure.", 2),
    "confused": ("Ignoring the confused is a neighbor failure.", 2),
    "burden": ("Ignoring the burdened is a neighbor failure.", 2),
    "fear-based": ("Fear-based tactics harm the neighbor.", 1),
    "rage bait": ("Rage bait harms the neighbor.", 0),
    "lust bait": ("Lust bait harms the neighbor.", 0),
    "vanity bait": ("Vanity bait harms the neighbor.", 0),
}

FRUIT_FLAGS = {
    "greed": ("Greed is bad fruit. Systems should not optimize for extraction.", 0),
    "pride": ("Pride is bad fruit. Systems should serve, not self-promote.", 1),
    "dependency": ("Creating dependency is bad fruit. Restore agency instead.", 0),
    "addiction": ("Addiction is bad fruit. Never design for compulsion.", 0),
    "confusion": ("Confusion is bad fruit. Clarity is the goal.", 1),
    "dominate": ("Domination is bad fruit. Service is the pattern.", 0),
    "control": ("Control over people is bad fruit. Stewardship, not domination.", 1),
    "vanity": ("Vanity is bad fruit. Humility produces good fruit.", 1),
    "deception": ("Deception is bad fruit. Truth is the foundation.", 0),
}

MAMMON_FLAGS = {
    "fake scarcity": ("Fake scarcity is mammon worship. Reject it.", 0),
    "fear funnel": ("Fear funnels are mammon worship. Serve, don't squeeze.", 0),
    "predatory": ("Predatory pricing is mammon worship.", 0),
    "spiritual pressure": ("Using spiritual pressure to sell is mammon worship.", 0),
    "hidden fee": ("Hidden fees are deception + mammon worship.", 0),
    "engagement trap": ("Engagement traps serve metrics, not people.", 1),
    "upsell": ("Aggressive upselling serves mammon, not the mission.", 2),
    "countdown": ("Artificial urgency (countdown timers) is fake scarcity.", 1),
    "limited spots": ("Fake scarcity ('only 3 spots') is mammon worship.", 1),
    "make money": ("If making money is the PRIMARY goal, mammon is at the wheel. Check motive.", 2),
    "get rich": ("'Get rich' promises are mammon worship.", 0),
    "guaranteed income": ("Guaranteed income claims are mammon worship. Never promise returns.", 0),
}

SERVICE_FLAGS = {
    "control people": ("Controlling people is not service. It's domination.", 0),
    "replace conscience": ("Replacing conscience with automation is not service.", 0),
    "replace god": ("Replacing God with AI is not service.", 0),
    "replace pastor": ("Replacing pastors with AI is not service. Augment, don't replace.", 0),
    "replace teacher": ("Replacing teachers with AI is not service. Augment, don't replace.", 0),
    "replace scripture": ("Replacing Scripture with AI output is not service.", 0),
    "increase power": ("Increasing owner power without blessing users is not service.", 1),
    "without blessing": ("Systems should bless everyone they touch, not just the owner.", 1),
}

# Positive indicators that raise scores
TRUTH_POSITIVE = ["honest", "truth", "transparent", "accurate", "real", "genuine", "humble", "limitation"]
NEIGHBOR_POSITIVE = ["serve", "help", "love", "care", "support", "encourage", "welcome", "include", "accessibility"]
FRUIT_POSITIVE = ["clarity", "wisdom", "peace", "healing", "growth", "freedom", "responsibility", "reconciliation"]
MAMMON_POSITIVE = ["fair", "honest pricing", "free", "donate", "accessible", "non-profit", "stewardship"]
SERVICE_POSITIVE = ["serve", "reduce burden", "restore", "empower", "teach", "guide", "help", "tool", "servant"]


def _score_test(text: str, flags: dict, positives: list, test_name: str) -> tuple[float, list[str]]:
    """Score a single test. Returns (score, notes)."""
    text_lower = text.lower()
    score = 5.0  # Start perfect, deduct for flags
    notes = []

    # Check for flags
    for keyword, (reason, deduction) in flags.items():
        if keyword in text_lower:
            score -= deduction
            notes.append(f"- {reason}")

    # Check for positive indicators
    positive_count = sum(1 for p in positives if p in text_lower)
    if positive_count >= 2:
        score = min(5.0, score + 0.5)
    if positive_count >= 4:
        score = min(5.0, score + 0.5)

    # Clamp
    score = max(0.0, min(5.0, score))

    # Add positive note if score is high
    if score >= 4.0 and not notes:
        notes.append(f"+ {test_name}: Strong alignment detected.")

    return score, notes


def evaluate_five_tests(agent_concept: str) -> FiveTestVerdict:
    """Run all Five Tests on an agent concept. Returns scores + verdict."""

    # Combine all text for analysis
    full_text = agent_concept

    # Score each test
    truth_score, truth_notes = _score_test(full_text, TRUTH_FLAGS, TRUTH_POSITIVE, "Truth")
    neighbor_score, neighbor_notes = _score_test(full_text, NEIGHBOR_FLAGS, NEIGHBOR_POSITIVE, "Neighbor")
    fruit_score, fruit_notes = _score_test(full_text, FRUIT_FLAGS, FRUIT_POSITIVE, "Fruit")
    mammon_score, mammon_notes = _score_test(full_text, MAMMON_FLAGS, MAMMON_POSITIVE, "Mammon")
    service_score, service_notes = _score_test(full_text, SERVICE_FLAGS, SERVICE_POSITIVE, "Service")

    composite = (truth_score + neighbor_score + fruit_score + mammon_score + service_score) / 5.0

    # Verdict logic
    scores = [truth_score, neighbor_score, fruit_score, mammon_score, service_score]
    if any(s == 0 for s in scores):
        verdict = "rejected"
    elif any(s <= 1 for s in scores):
        verdict = "needs_correction"
    elif composite < 3.0:
        verdict = "needs_correction"
    elif all(s >= 4 for s in scores):
        verdict = "good_fruit"
    else:
        verdict = "approved"

    # Compile correction notes
    correction_notes = {}
    all_notes = {
        "Truth": truth_notes,
        "Neighbor": neighbor_notes,
        "Fruit": fruit_notes,
        "Mammon": mammon_notes,
        "Service": service_notes,
    }
    for test_name, notes in all_notes.items():
        if notes:
            correction_notes[test_name] = "\n".join(notes)

    return FiveTestVerdict(
        truth_score=round(truth_score, 1),
        neighbor_score=round(neighbor_score, 1),
        fruit_score=round(fruit_score, 1),
        mammon_score=round(mammon_score, 1),
        service_score=round(service_score, 1),
        composite=round(composite, 2),
        verdict=verdict,
        correction_notes=correction_notes,
    )
