# Loop Plan
## Mode
build
## Goal
Implement 24 General Accounting components in SME Accounting project following discovery-first TDD rules
## Stop Condition
all tasks in loop-stack/implement-gen-acct-02/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Discover existing General Accounting entities, ports, EF configurations and architecture constraints via code exploration
- [x] [G1] Discover missing Bank/BankBranch/BankAccount entities and verify PostingReference implementation gaps
- [x] [G1] Extract company isolation, effective dating, soft delete, enum storage patterns for implementation reference
- [x] [G2] Implement Bank aggregate with Domain entity, EF configuration, repository, Application commands/queries and FluentValidation using TDD
- [ ] [G2] Implement BankBranch and BankAccount domain entities with EF configurations, repositories and Application layer with TDD
- [ ] [G3] Verify architecture compliance, run build and architecture tests, create minimal integration tests for Bank components
