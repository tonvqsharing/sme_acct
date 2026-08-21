# Todo — Company Module (Root Aggregate)

## Slice 1: Domain enums + exceptions
- [ ] S1.1: Create `src/bricks/company/__init__.py`
- [ ] S1.2: Create `src/bricks/company/domain.py` — enums (CompanyType, CompanyStatus, AccountingRegime)
- [ ] S1.3: Add Company dataclass, BankAccount dataclass, TaxId value object
- [ ] S1.4: Add domain exceptions (CompanyError, DuplicateMSTError, etc.)
- [ ] S1.5: Write `tests/unit/company/__init__.py`
- [ ] S1.6: Write `tests/unit/test_company_enums.py` (RED)
- [ ] S1.7: Write `tests/unit/test_company_domain.py` (RED)
- [ ] S1.8: Run tests, verify RED

## Slice 2: Contract interface
- [ ] S2.1: Create `src/bricks/company/contract.py` — CompanyRepositoryPort
- [ ] S2.2: Write `tests/unit/test_company_contract.py`
- [ ] S2.3: Run tests, verify GREEN

## Slice 3: Storage layer
- [ ] S3.1: Create `src/bricks/company/storage.py` — CompanyModel
- [ ] S3.2: Implement SQLAlchemyCompanyRepository
- [ ] S3.3: Write `tests/integration/test_company_repository.py`
- [ ] S3.4: Run tests, verify GREEN

## Slice 4: Service layer
- [ ] S4.1: Create `src/bricks/company/services.py` — CompanyService
- [ ] S4.2: Implement TenantService
- [ ] S4.3: Write `tests/unit/test_company_service.py`
- [ ] S4.4: Run tests, verify GREEN

## Slice 5: Web adapter
- [ ] S5.1: Create `src/bricks/company/web_adapter.py` — companies_bp
- [ ] S5.2: Implement REST endpoints
- [ ] S5.3: Write `tests/integration/test_company_api.py`
- [ ] S5.4: Run tests, verify GREEN

## Slice 6: App registration + migration
- [ ] S6.1: Register blueprint in `src/app.py`
- [ ] S6.2: Create migration file
- [ ] S6.3: Verify migration applies

## Slice 7: Quality gates
- [ ] S7.1: Run ruff check
- [ ] S7.2: Run black --check
- [ ] S7.3: Run mypy
- [ ] S7.4: Run full pytest suite

## Slice 8: Docs + git
- [ ] S8.1: Update docs status
- [ ] S8.2: codegraph sync
- [ ] S8.3: git commit
