# Skill Decision Tables (5W1H)

## Table 1 — By Development Phase

| Phase | Stage | Skill | WHEN to trigger | WHY | HOW |
|-------|-------|-------|-----------------|-----|-----|
| **DEFINE** | Requirements | `interview-me` | Ask is underspecified, ambiguous | Extract true intent before planning | One-question-at-a-time interview |
| **DEFINE** | Idea shaping | `idea-refine` | Idea is vague, need to stress-test | Divergent + convergent thinking | Structured ideation session |
| **DEFINE** | Requirements | `spec-driven-development` | No spec exists, starting new feature | Write requirements before code | Spec document creation |
| **DEFINE** | Domain terms | `ubiquitous-language` | Need domain glossary, DDD terms | Establish shared vocabulary | Extract + flag ambiguities |
| **DEFINE** | Domain model | `domain-modeling` | Need to pin down domain concepts | Sharpen domain understanding | Model extraction + ADR |
| **DEFINE** | Questionnaire | `to-questionnaire` | Decision needs input from others | Delegate decision to stakeholder | Generate fillable questionnaire |
| **DESIGN** | Interface | `api-and-interface-design` | Designing APIs, module boundaries | Stable public contracts | Interface design guidance |
| **DESIGN** | Interface options | `design-an-interface` | Want multiple design options | Compare radically different shapes | Parallel sub-agent generation |
| **DESIGN** | Architecture | `codebase-design` | Improve module interfaces, find seams | Deep module design vocabulary | Design review + suggestions |
| **DESIGN** | Architecture scan | `improve-codebase-architecture` | Scan for deepening opportunities | Find architectural improvements | HTML report + grill session |
| **DESIGN** | Planning | `planning-and-task-breakdown` | Have spec, need task list | Break work into implementable steps | Task decomposition |
| **DESIGN** | Tickets | `to-tickets` | Need work items on tracker | Tracer-bullet tickets with edges | Ticket generation |
| **DESIGN** | Large planning | `wayfinder` | Huge work chunk, multi-session | Map decision tickets for tracking | Issue tracker planning |
| **DESIGN** | Prototype | `prototype` | Sanity-check design question | Quick throwaway validation | Build prototype |
| **DESIGN** | Stress test | `grill-me` | Sharpen a plan or design | Relentless interview | Adversarial Q&A |
| **DESIGN** | Stress test + docs | `grill-with-docs` | Sharpen plan + record decisions | Interview + ADR creation | Grill + doc generation |
| **DESIGN** | Stress test (user) | `grilling` | User wants to stress-test thinking | Challenge assumptions | Relentless questioning |
| **DESIGN** | Refactor plan | `request-refactor-plan` | Plan a refactor, create RFC | Safe incremental steps | Interview + issue filing |
| **IMPLEMENT** | Coding | `implement` | Have spec/tickets, need code | Execute implementation | Code generation |
| **IMPLEMENT** | Incremental | `incremental-implementation` | Feature touches many files | Land changes in safe steps | Chunked delivery |
| **IMPLEMENT** | TDD | `tdd` | Build test-first, red-green-refactor | Prove code works | Test-driven cycle |
| **IMPLEMENT** | TDD (alt) | `test-driven-development` | Implement logic, fix bug, change behavior | Verify with tests | Test-first development |
| **IMPLEMENT** | Source-correct | `source-driven-development` | Framework/library correctness matters | Authoritative, source-cited code | Documentation-grounded impl |
| **IMPLEMENT** | Deep modules | `setup-ts-deep-modules` | TypeScript repo needs module boundaries | Implementation hidden in subfolders | Wire dependency-cruiser |
| **QUALITY** | Code review | `code-review` | Review changes since commit/branch | Standards + spec compliance | Parallel review agents |
| **QUALITY** | Code review (multi) | `code-review-and-quality` | Before merging any change | Multi-axis quality assessment | Quality gate review |
| **QUALITY** | Simplify | `code-simplification` | Code works but is too complex | Reduce unnecessary complexity | Refactor for clarity |
| **QUALITY** | Karpathy check | `karpathy-guidelines` | Writing/reviewing/refactoring code | Avoid common LLM mistakes | 4-principle checklist |
| **QUALITY** | Doubt check | `doubt-driven-development` | High stakes, unfamiliar code | Adversarial verification before shipping | Fresh-context review |
| **QUALITY** | Security | `security-and-hardening` | User input, auth, data storage | Prevent vulnerabilities | Security-first practices |
| **QUALITY** | Performance | `performance-optimization` | Perf regressions, N+1 queries, slow loads | Fix bottlenecks | Profiling + optimization |
| **QUALITY** | Observability | `observability-and-instrumentation` | Shipping production features | Make behavior visible | Logging/metrics/tracing setup |
| **QUALITY** | Browser test | `browser-testing-with-devtools` | Building/debugging browser code | Real runtime verification | Chrome DevTools MCP |
| **QUALITY** | QA session | `qa` | Report bugs conversationally | File issues from discussion | Interactive QA → GitHub issues |
| **QUALITY** | Diagnose bugs | `diagnosing-bugs` | Hard bugs, performance regressions | Systematic root-cause analysis | Diagnosis loop |
| **QUALITY** | Debug | `debugging-and-error-recovery` | Tests fail, builds break, unexpected errors | Find and fix root cause | Systematic debugging |
| **TEST** | Integration | `migrate-to-shoehorn` | Replace `as` in tests with shoehorn | Partial test data patterns | Test migration |
| **DELIVER** | Git workflow | `git-workflow-and-versioning` | Any code change, commits, releases | Structured version control | Git flow guidance |
| **DELIVER** | Merge conflicts | `resolving-merge-conflicts` | In-progress merge/rebase conflict | Resolve cleanly | Conflict resolution |
| **DELIVER** | Pre-commit | `setup-pre-commit` | Add commit-time quality gates | Lint-staged + Husky setup | Hook configuration |
| **DELIVER** | CI/CD | `ci-cd-and-automation` | Set up build/deploy pipelines | Automate quality gates | Pipeline configuration |
| **DELIVER** | Ship | `shipping-and-launch` | Preparing for production deploy | Launch checklist + rollback | Pre-launch preparation |
| **DELIVER** | Wizard | `wizard` | Manual procedure needs automation | Walk human through setup | Generate bash wizard |
| **DOCUMENT** | ADRs | `documentation-and-adrs` | Architectural decisions, API changes | Record context for future | ADR + docs creation |
| **DOCUMENT** | Ref docs | `research` | Need topic researched, docs gathered | Delegate reading to agent | Research note capture |
| **DOCUMENT** | Write article | `writing-fragments` | Mining raw material, no structure yet | Explore what could be written | Fragment generation |
| **DOCUMENT** | Write article | `writing-beats` | Assembling material into journey | Ground terms before beats | Beat assembly |
| **DOCUMENT** | Write article | `writing-shape` | Shaping material into article | Paragraph-by-paragraph shaping | Article construction |
| **DOCUMENT** | Edit article | `edit-article` | Improve existing article draft | Restructure + tighten prose | Article editing |
| **MAINTAIN** | Deprecation | `deprecation-and-migration` | Removing old systems/APIs | Safe migration path | Deprecation management |
| **MAINTAIN** | Refactor plan | `request-refactor-plan` | Need refactoring RFC | Tiny commits, safe steps | Interview + issue |
| **OPS** | Obsidian | `obsidian-vault` | Find/create/organize notes | Vault management | Note operations |
| **OPS** | Obsidian search | `qmd` | Search vault semantically | Find past decisions/patterns | QMD semantic search |
| **OPS** | Obsidian markdown | `obsidian-markdown` | Create/edit .md in Obsidian | Wikilinks, callouts, props | Markdown formatting |
| **OPS** | Obsidian CLI | `obsidian-cli` | CLI vault operations, plugin dev | Read/create/search notes | CLI commands |
| **OPS** | Obsidian bases | `obsidian-bases` | Create database-like views | Table/card views with filters | .base file creation |
| **OPS** | JSON Canvas | `json-canvas` | Create visual canvases/mind maps | Node-edge diagrams | .canvas file creation |

## Table 2 — By User Intent

| User Says… | Intent | Recommended Skill | Alternative |
|------------|--------|-------------------|-------------|
| "build me X" (vague) | Underspecified need | `interview-me` | `grill-me` |
| "I have an idea" | Idea exploration | `idea-refine` | `grill-me` |
| "design an API" | Interface design | `api-and-interface-design` | `design-an-interface` |
| "design it twice" | Multiple options | `design-an-interface` | — |
| "write a spec" | Requirements | `spec-driven-development` | `to-spec` |
| "break this down" | Task planning | `planning-and-task-breakdown` | `to-tickets` |
| "implement this" | Code generation | `implement` | `incremental-implementation` |
| "make it test-first" | TDD | `tdd` | `test-driven-development` |
| "review my code" | Code review | `code-review-and-quality` | `code-review` |
| "simplify this" | Refactor | `code-simplification` | `karpathy-guidelines` |
| "what's wrong?" | Debug | `debugging-and-error-recovery` | `diagnosing-bugs` |
| "it's slow" | Performance | `performance-optimization` | `diagnosing-bugs` |
| "add logging" | Observability | `observability-and-instrumentation` | — |
| "test in browser" | Browser testing | `browser-testing-with-devtools` | — |
| "ship it" | Deploy prep | `shipping-and-launch` | `ci-cd-and-automation` |
| "commit this" | Git workflow | `git-workflow-and-versioning` | — |
| "document this" | Documentation | `documentation-and-adrs` | `research` |
| "what should I use?" | Skill routing | `ask-matt` | `using-agent-skills` |
| "grill me" | Stress test | `grilling` | `grill-me` |
| "I need a refactor" | Refactoring | `request-refactor-plan` | `improve-codebase-architecture` |
| "set up hooks" | Pre-commit | `setup-pre-commit` | `git-guardrails-claude-code` |
| "create a wizard" | Manual procedure | `wizard` | — |
| "file an issue" | QA/bug report | `qa` | `triage` |
| "research X" | Information gathering | `research` | `defuddle` (for URLs) |
| "teach me X" | Learning | `teach` | — |
| "hand off" | Context transfer | `handoff` | `claude-handoff` |
| "what's the status?" | Progress check | `dev-standup` | — |

## Table 3 — By Agent Role

| Agent Role | Primary Skills | Support Skills |
|------------|---------------|----------------|
| **Researcher** | `research`, `qmd`, `defuddle` | `source-driven-development`, `knowledge-sources/*` |
| **Planner** | `planning-and-task-breakdown`, `to-tickets`, `wayfinder` | `idea-refine`, `spec-driven-development` |
| **Implementer** | `implement`, `incremental-implementation`, `tdd` | `karpathy-guidelines`, `source-driven-development` |
| **Reviewer** | `code-review`, `code-review-and-quality`, `doubt-driven-development` | `karpathy-guidelines`, `security-and-hardening` |
| **Debugger** | `debugging-and-error-recovery`, `diagnosing-bugs` | `observability-and-instrumentation` |
| **Architect** | `codebase-design`, `improve-codebase-architecture`, `domain-modeling` | `api-and-interface-design`, `documentation-and-adrs` |
| **Scribe** | `documentation-and-adrs`, `ubiquitous-language` | `writing-beats`, `writing-shape` |
| **Ops** | `ci-cd-and-automation`, `shipping-and-launch`, `observability-and-instrumentation` | `setup-pre-commit`, `git-guardrails-claude-code` |
| **Orchestrator** | `loop-engineer`, `wayfinder`, `handoff` | `ask-matt`, `using-agent-skills` |

## Table 4 — By Skill Trigger Type

| Trigger | Skills |
|---------|--------|
| **Autonomous** (agent fires) | `karpathy-guidelines`, `using-agent-skills`, `ask-matt`, `qmd` |
| **User-invoked** (explicit) | `tdd`, `grilling`, `grill-me`, `teach`, `wizard`, `handoff`, `qa`, `triage` |
| **Phase-gated** (workflow step) | `implement`, `code-review`, `documentation-and-adrs`, `git-workflow-and-versioning` |
| **Event-driven** (something happened) | `debugging-and-error-recovery`, `resolving-merge-conflicts`, `deprecation-and-migration` |
| **Quality gate** (before merge/ship) | `code-review-and-quality`, `security-and-hardening`, `doubt-driven-development`, `test-driven-development` |

## Table 5 — Skill Combinations (Common Workflows)

| Workflow | Skills in Order | Output |
|----------|----------------|--------|
| **New feature** | `interview-me` → `spec-driven-development` → `planning-and-task-breakdown` → `implement` → `tdd` → `code-review-and-quality` → `documentation-and-adrs` | Feature shipped with docs |
| **Bug fix** | `debugging-and-error-recovery` → `tdd` → `implement` → `code-review` → `git-workflow-and-versioning` | Fix committed |
| **Refactor** | `improve-codebase-architecture` → `grill-me` → `request-refactor-plan` → `implement` → `code-review-and-quality` | Safe refactor |
| **API design** | `api-and-interface-design` → `design-an-interface` → `grill-with-docs` → `implement` | API designed + implemented |
| **Production issue** | `diagnosing-bugs` → `observability-and-instrumentation` → `debugging-and-error-recovery` → `shipping-and-launch` | Issue resolved + monitored |
| **Writing** | `writing-fragments` → `grilling` → `writing-beats` → `writing-shape` → `edit-article` | Article published |
| **Large project** | `wayfinder` → `loop-engineer` (per ticket) → `handoff` between sessions | Multi-session delivery |
| **Security audit** | `security-and-hardening` → `doubt-driven-development` → `code-review-and-quality` → `documentation-and-adrs` | Hardened + documented |
