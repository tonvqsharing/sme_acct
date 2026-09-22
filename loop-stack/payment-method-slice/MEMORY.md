# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
- [G1] PaymentMethod design doc written to docs/PaymentMethod-Design-2026.md (164 lines, 0 placeholders): PaymentTerm 1:1 copy with PaymentTermType/Days swapped for PaymentMethodCategory/RequiresBankAccount(bool default false); enum PaymentMethodCategory (Cash/BankTransfer/Card/EWallet/Other) in Domain/ValueObjects with HasConversion<string>; constraints composite unique (CompanyId,Code) + Company FK Restrict + xmin + snake_case payment_methods; no Bank/Journal FKs; DomainException + FluentValidation matrix (20/200/500 + IsInEnum); UNKNOWN-1..4 resolved, UNKNOWN-5/6 carried forward.
