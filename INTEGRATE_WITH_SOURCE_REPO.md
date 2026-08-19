# Integrating this release with the existing `prx0r/Alethiea` repository

This archive is the cleaned release kernel/submission pack produced from review of source HEAD `9c8d90f9d4e1bb42299daacd6bd0aa3e9046fc12`. It is intentionally not a byte-for-byte clone of the full source repository.

If applying it back to the existing repository, preserve useful experimental modules that are not in this release (for example deeper attestation, Merkle, peer-review or lineage experiments) **behind the core release surface** rather than deleting them blindly.

## Required source changes

1. Add `patala_research_ci/relations.py` from this archive.
2. Replace the source relation comparison in `patala_research_ci/diff.py` with semantic `relation_key()` comparison.
3. Make relation dependency matching in `impact.py` use the same canonical semantic representation.
4. Preserve raw relation observations in snapshots; canonicalize at comparison/impact boundaries.
5. Add the inverse-relation regression tests from `tests/test_relations.py` and `tests/test_diff.py`.
6. Replace the stale root `demo.py` with this release's wrapper/canonical CLI demo.
7. Update `pyproject.toml` repository URLs and add the `aletheia` console alias.
8. Replace judge-facing README/DEMO/VIDEO/SUBMISSION/PITCH documents with this release pack.
9. Move `IDEAS*.md`, old pitch drafts, criteria self-scores and alternate-build brainstorming into `docs/archive/` or a development branch so they do not compete with the final artifact.
10. Keep the source project's advanced provenance modules only if their tests still pass against the canonical relation/model changes.

## Acceptance checks

```bash
python -m unittest discover -s tests -v
python scripts/verify_release.py
python -m patala_research_ci --workspace /tmp/aletheia-demo demo
```

The demo must show:

```text
Representation-only citation change emitted: NO
claim:dataset-coverage       RECOMPUTE_REQUIRED
claim:citation-path          CURRENT
claim:access-right           CURRENT
recomputed dataset coverage  UNSUPPORTED (0.25)
ledger                       VERIFIED
```

Do not merge if an `IsCitedBy(A,B) → Cites(B,A)` migration creates a material relation addition/removal.
