# Agent Skill Decision Guide

## Purpose
Compact decision table to select the right OpenCode skill for each task using 5W1H.

## Skill Decision Table

| Skill | Who | What | When | Where | Why | How |
|-------|-----|------|------|-------|-----|-----|
| ask-matt / using-agent-skills | User/Agent unsure | Route to skill | Start of session / ambiguous ask | Any | Pick correct workflow | Ask “which skill fits?” |
| planning-and-task-breakdown | Planner | Ordered tasks from spec | Spec exists, work too large | Repo planning | Make work implementable/parallel | “break down this task” |
| spec-driven-development | Architect | Spec before code | New feature/project, requirements unclear | Design phase | Reduce ambiguity | “create spec first” |
| source-driven-development | Implementer | Official-doc grounded code | Framework/library work, correctness matters | Implementation | Avoid outdated patterns | Require source citations |
| implement | Developer | Build from spec/tickets | Spec ready | Codebase | Execute plan | “implement spec” |
| incremental-implementation | Developer | Deliver changes in small steps | Multi-file change, large | Codebase | Reduce risk | Small commits per step |
| tdd / test-driven-development | Developer | Tests first then code | New logic, bug fix | Tests + src | Prove correctness | Red-Green-Refactor |
| code-simplification | Refactorer | Clarify code, same behavior | Code works but hard to read/maintain | Codebase | Maintainability | Refactor without changing tests |
| debugging-and-error-recovery / diagnosing-bugs | Developer | Root-cause debug | Tests fail, build breaks, bug/ slow | Runtime/CI | Find cause | Systematic reproduction |
| security-and-hardening | Security engineer | Harden input/auth/storage | Untrusted data, auth, external integration | Codebase | Prevent vulns | Threat model + fixes |
| performance-optimization | Perf engineer | Optimize frontend/backend/DB | Perf reqs, regression, Core Web Vitals | App | Meet SLAs | Profile, N+1, caching |
| observability-and-instrumentation | SRE | Logging/metrics/tracing/alerting | Production opaque | Prod code | Diagnose incidents | Add telemetry |
| ci-cd-and-automation | DevOps | Pipeline setup | New repo/CI change | .github/workflows | Quality gates | Automate build/test/deploy |
| shipping-and-launch | Release lead | Pre-launch checklist, rollout/rollback | Go-live | Production | Safe launch | Checklist + monitoring |
| code-review-and-quality / code-review | Reviewer | Multi-axis review | Before merge / PR | Repo | Standards + spec | Parallel Standards/Spec review |
| documentation-and-adrs | Architect | Record decisions | Architectural change, API change, feature ship | docs/ | Future context | ADR + docs |
| domain-modeling / ubiquitous-language | DDD team | Domain model + glossary | Terminology ambiguity | Domain | Shared understanding | Extract glossary |
| deprecation-and-migration | Maintainer | Sunset old APIs | Legacy removal | Codebase | Reduce tech debt | Migration plan |
| api-and-interface-design | Designer | Stable API contracts | New public interface | Modules | Compatibility | Design alternatives |
| design-an-interface | Designer | Multiple radical designs | Explore options | Design phase | Compare shapes | Parallel sub-agents |
| codebase-design | Architect | Deep module seams | Improve testability/AI-navigability | Modules | Better boundaries | Identify seams |
| frontend-ui-engineering | UI engineer | Production UI | UI pages/components | Frontend | Accessibility/responsive | WCAG standards |
| browser-testing-with-devtools | QA | Real browser checks | DOM/network/perf bugs | Browser | Real runtime | DevTools MCP |
| qa | QA | File issues from bug reports | Bug reporting session | Repo | Track defects | Conversational issue filing |
| git-workflow-and-versioning | Developer | Commit/branch/release | Any code change | Repo | History hygiene | Conventional commits, tags |
| resolving-merge-conflicts | Developer | Fix merge/rebase conflict | Conflict state | Git | Unblock | Resolve in-progress |
| setup-pre-commit | DevOps | Husky hooks | Repo setup | Repo root | Quality gates | lint-staged + tests |
| research | Researcher | Primary-source findings | Need docs/API facts | Web | Accurate info | Markdown report |

## 5W1H Quick Selector

### Who is asking?
- Unsure → ask-matt, using-agent-skills
- Planner → planning-and-task-breakdown, wayfinder
- Architect → spec-driven-development, documentation-and-adrs, domain-modeling, codebase-design
- Developer → implement, incremental-implementation, tdd, debugging-and-error-recovery
- Reviewer → code-review-and-quality, code-review
- Security → security-and-hardening
- DevOps → ci-cd-and-automation, shipping-and-launch, setup-pre-commit

### What is the task type?
- Design API → api-and-interface-design, design-an-interface
- Refactor for clarity → code-simplification
- Fix bug → diagnosing-bugs, tdd
- Add tests → test-driven-development
- Write docs/ADR → documentation-and-adrs
- Migrate/deprecate → deprecation-and-migration
- Improve perf → performance-optimization
- Add observability → observability-and-instrumentation
- UI work → frontend-ui-engineering, browser-testing-with-devtools
- Git workflow → git-workflow-and-versioning, resolving-merge-conflicts

### When to trigger?
- Start/no spec → spec-driven-development, planning-and-task-breakdown
- Before merge → code-review-and-quality
- Production issue → observability-and-instrumentation, diagnosing-bugs
- Launch → shipping-and-launch
- Ambiguous request → ask-matt, interview-me

### Where in repo?
- Module boundaries → codebase-design, api-and-interface-design
- Domain language → domain-modeling, ubiquitous-language
- CI files → ci-cd-and-automation, setup-pre-commit
- Docs → documentation-and-adrs, edit-article

### Why choose it?
- Correctness over speed → doubt-driven-development
- Token efficiency → caveman
- Context overload → context-engineering
- Need authoritative sources → source-driven-development

### How to invoke?
Use trigger phrases:
- “design it twice” → design-an-interface
- “red-green-refactor” → tdd
- “review since X” → code-review
- “caveman mode” → caveman
- “spec before code” → spec-driven-development
- “incremental” → incremental-implementation

## Decision Flow
Who → What → When → Where → Why → How → pick skill from table.

If mapping unclear, use ask-matt.
