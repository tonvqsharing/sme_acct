# Loop Plan
## Mode
build
## Goal
Build complete Product & Inventory Foundation for Vietnamese accounting web application integrating P1-P4
## Stop Condition
all tasks in loop-stack/product-inventory-foundation/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Implement UOM domain entity, event, port, EF config, repository, application CQRS commands/queries, FluentValidation, API controller, and migration
- [ ] [G1] Implement Item Category domain entity with self-reference hierarchy, EF config, repository, application CQRS, API controller, migration
- [ ] [G1] Implement Warehouse domain entity, EF config, repository, application CQRS, API controller, migration
- [ ] [G2] Implement UOM Conversion domain entity with invariants, EF config, repository, application CQRS, API controller, migration
- [ ] [G2] Implement Item/Product and Service Item domain entities with relationships to Category/UOM, EF configs, repositories, application CQRS, API controllers, migration
- [ ] [G2] Implement Inventory Valuation Policy and Inventory Adjustment Reason domain entities, EF configs, repositories, application CQRS, API controllers, migration
- [ ] [G3] Implement Inventory Accounting Configuration domain entity linking Accounts and Valuation Policy, EF config, repository, application CQRS, API controller, migration, and integration verification with P1-P4
