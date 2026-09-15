# Loop Plan
## Mode
build
## Goal
Implement complete authorization system in SmeAccounting.Modules.Authorization: roles, permissions, policy-based access
## Stop Condition
all tasks in loop-stack/auth-module-roles/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Discover module structure and design domain entities for Authorization
- [x] [G1] Implement Domain layer: Role, Permission, RolePermission aggregates, value objects, domain events
- [x] [G2] Implement Application layer: CQRS commands/queries, handlers, validators, permission policy provider/handler
- [x] [G2] Implement Infrastructure layer: EF configurations, repositories, DbContext integration, module registration
- [x] [G3] Create migrations and seed roles/permissions data
- [x] [G3] Write unit/integration tests and architecture tests
- [ ] [G4] Update documentation, run review, handoff
