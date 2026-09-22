# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
- [G1] 2026-09-22: locked Option 2 domain-only in docs/SetSource-CallerFix-Design-2026.md — 3 SetSource guards (posted/type/id, verbatim messages) + 1 caller fail-fast `Id<=0` pre-condition before JE build; line 78 literal unchanged; 2-file touch boundary; discard bug + null/null path + PostingReference + EF explicitly no-touch; design-only, zero code diff.
