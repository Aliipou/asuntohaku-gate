# Operating brief — asuntohaku-gate

Read `asuntohaku-gate-SPEC.md` first. It is the contract. This file covers how
to work, not what to build.

## Standing rules

- Build in the order given in section 12. The rule engine and its tests come
  before any UI. If you find yourself writing a React component before the rule
  tests are green, stop.
- Never produce an eligibility outcome without a rule id, a Finnish message and
  non-empty evidence. If a code path needs one, the design is wrong — fix the
  design, do not add a default.
- Rules stay pure. If a rule needs the current date or a threshold, it is
  passed in as an argument. No `datetime.now()`, no session, no query inside a
  rule module.
- `puuttuvat_tiedot` is a real outcome, not an error state. Missing input never
  becomes a rejection.
- All user-facing strings are Finnish. Keep them in one place. Do not scatter
  Finnish literals through components.
- Thresholds live only in `seeds/limits.py`. If a number appears anywhere else,
  it is a bug.

## What not to do

- Do not add authentication, an LLM, a component library, or a state management
  library. The spec names the stack; anything outside it needs a reason written
  in the commit message.
- Do not inflate the test count with trivial assertions.
- Do not write claims in the README that the code does not support. If
  something is unimplemented, say so in the limitations section rather than
  softening the description.
- Do not use placeholder Lorem text. Write real Finnish apartment descriptions
  in the seed data.

## Commits

Small and self-describing. One commit per spec section where possible. The
message says what changed and why, not "update files".

## When something in the spec is wrong

The spec was written before the code. If a constraint turns out to be
impossible or actively bad, say so in the session and propose the change —
do not silently work around it and do not implement it badly to satisfy the
letter of it.
