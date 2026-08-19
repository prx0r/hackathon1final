#!/usr/bin/env python3
"""3-Change Demo: Irrelevant, Representational, Evidence.

Demonstrates why Aletheia is not just 'git diff for JSON'.

Change 1: Publisher metadata changes → CURRENT (irrelevant)
Change 2: IsCitedBy(A,B) → Cites(B,A) → CURRENT (semantic equivalence)
Change 3: Dataset D supports Publication P relation removed → RECHECK (evidence)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from patala_research_ci.model import Snapshot, SourceStatus, TrackedClaim, Dependency


def make_snapshot(items, relations, status="OK"):
    return Snapshot(
        snapshot_id="snap:test",
        provider="openaire",
        api_version="v3",
        observed_at="2026-08-19T00:00:00Z",
        query={"search": "test"},
        source_status=status,
        source_error=None,
        items=items,
        relations=relations,
        header={"numFound": len(items)},
        digest="",
    )


def run():
    print("=" * 70)
    print("3-CHANGE DEMO: Why Aletheia is not just git diff for JSON")
    print("=" * 70)

    # ─── BASELINE STATE ───
    print("\n[BASELINE] OpenAIRE state at T1")
    print("─" * 50)

    old_items = [
        {"id": "openaire::paper-A", "title": "Paper A", "type": "publication",
         "publisher": "Oxford University Press", "publicationDate": "2023-01-15"},
        {"id": "openaire::paper-B", "title": "Paper B", "type": "publication",
         "publisher": "Springer", "publicationDate": "2022-06-20"},
        {"id": "openaire::dataset-D", "title": "Dataset D", "type": "dataset",
         "access_right": "OPEN"},
    ]

    old_relations = [
        {"source": "openaire::paper-A", "relation": "IsCitedBy", "target": "openaire::paper-B"},
        {"source": "openaire::dataset-D", "relation": "IsSupplementTo", "target": "openaire::paper-A"},
    ]

    old_snapshot = make_snapshot(old_items, old_relations)

    for item in old_items:
        print(f"  {item['id']}: {item['title']}")
    for rel in old_relations:
        print(f"  {rel['source']} --[{rel['relation']}]--> {rel['target']}")

    # ─── CHANGED STATE ───
    print("\n[CHANGED] OpenAIRE state at T2 (3 changes)")
    print("─" * 50)

    new_items = [
        {"id": "openaire::paper-A", "title": "Paper A", "type": "publication",
         "publisher": "Oxford University Press", "publicationDate": "2023-01-15"},
        {"id": "openaire::paper-B", "title": "Paper B", "type": "publication",
         "publisher": "Cambridge University Press", "publicationDate": "2022-06-20"},  # CHANGE 1: publisher
        {"id": "openaire::dataset-D", "title": "Dataset D", "type": "dataset",
         "access_right": "OPEN"},
    ]

    new_relations = [
        {"source": "openaire::paper-B", "relation": "Cites", "target": "openaire::paper-A"},  # CHANGE 2: IsCitedBy → Cites
        # CHANGE 3: dataset-D → paper-A relation REMOVED
    ]

    new_snapshot = make_snapshot(new_items, new_relations)

    print("  Changes applied:")
    print("    1. Paper B publisher: 'Springer' → 'Cambridge University Press'")
    print("    2. Relation: IsCitedBy(A,B) → Cites(B,A)")
    print("    3. Relation: dataset-D → paper-A REMOVED")

    # ─── CLAIMS ───
    print("\n[CLAIMS] Agent conclusions from T1")
    print("─" * 50)

    claims = [
        TrackedClaim(
            claim_id="claim:citation-network",
            text="Paper A is cited by Paper B",
            dependencies=[Dependency(kind="relation", source="openaire::paper-A",
                                     relation="IsCitedBy", target="openaire::paper-B")],
        ),
        TrackedClaim(
            claim_id="claim:dataset-support",
            text="Dataset D supports Paper A",
            dependencies=[Dependency(kind="relation", source="openaire::dataset-D",
                                     relation="IsSupplementTo", target="openaire::paper-A")],
        ),
        TrackedClaim(
            claim_id="claim:paper-exists",
            text="Paper A exists with publisher Oxford",
            dependencies=[Dependency(kind="entity", entity_id="openaire::paper-A")],
        ),
    ]

    for c in claims:
        print(f"  {c.claim_id}: {c.text}")

    # ─── RUN DIFF ───
    print("\n[DIFF] Comparing T1 → T2")
    print("─" * 50)

    from patala_research_ci.diff import diff_snapshots
    diff = diff_snapshots("demo", old_snapshot, new_snapshot)

    print(f"  Changes detected: {len(diff.changes)}")
    for c in diff.changes:
        print(f"    {c.kind}: {c.reason}")
        if c.relation:
            print(f"      {c.relation}")

    # ─── IMPACT ───
    print("\n[IMPACT] Which claims are affected?")
    print("─" * 50)

    from patala_research_ci.impact import compute_impact
    impact = compute_impact("demo", diff, claims)

    for imp in impact.claims:
        state = imp.state
        if state == "CURRENT":
            icon = "CURRENT"
        elif state == "RECOMPUTE_REQUIRED":
            icon = "RECHECK"
        else:
            icon = state
        print(f"  {imp.claim_id:25s} {icon}")
        if imp.reasons:
            for r in imp.reasons:
                print(f"    {r}")

    # ─── THE STORY ───
    print("\n" + "=" * 70)
    print("THE STORY")
    print("=" * 70)
    print("""
CHANGE 1: Publisher metadata changed
  Paper B publisher: 'Springer' → 'Cambridge University Press'
  Claim: 'Paper A is cited by Paper B'
  Result: CURRENT
  Why: publisher field is not in the claim's dependency list

CHANGE 2: IsCitedBy(A,B) → Cites(B,A)
  Same scholarly proposition, different edge type
  Claim: 'Paper A is cited by Paper B'
  Result: CURRENT
  Why: relation canonicalization detects semantic equivalence
       IsCitedBy(A,B) ≡ Cites(B,A)

CHANGE 3: Dataset D → Paper A relation REMOVED
  Dataset support relation disappeared
  Claim: 'Dataset D supports Paper A'
  Result: RECHECK
  Why: direct dependency on the removed relation

THIS IS WHY ALETHEIA IS NOT GIT DIFF FOR JSON:
  Git diff would flag ALL 3 changes.
  Aletheia correctly identifies that only CHANGE 3 matters.

  Change 1: irrelevant (metadata not in dependency list)
  Change 2: representational (same proposition, different form)
  Change 3: evidence (relation actually removed)
""")


if __name__ == "__main__":
    run()
