# IFRS Transition Roadmap

## Overview

Decision 345/QĐ-BTC (2020) defines phased IFRS adoption in Vietnam. The accounting engine needs an abstraction layer for accounting policies (VAS vs IFRS) to support future transition.

## Decision 345/QĐ-BTC Phases

| Phase | Period | Scope | Action |
|-------|--------|-------|--------|
| Phase I | 2022-2025 | Voluntary | Listed companies and large enterprises may voluntarily apply IFRS |
| Phase II | Post-2025 | Compulsory (consolidated) | Mandatory for consolidated financial statements of SOEs, listed, and large non-listed companies |

## Key Differences VAS vs IFRS

| Aspect | VAS | IFRS |
|--------|-----|------|
| Approach | Rules-based | Principles-based |
| COA | Prescribed format | No prescribed format |
| Valuation | Historical cost dominant | Fair value emphasis |
| Leases (VAS 06 vs IFRS 16) | Operating lease = periodic expense | ROU asset + lease liability |
| Revenue (VAS 14 vs IFRS 15) | Point of transfer | Five-step model |
| Financial Instruments | No IFRS 9 equivalent | IFRS 9 recognition/measurement |
| Tax (VAS 17 vs IAS 12) | Deferred tax limited to carry-forward losses | Broader deferred tax recognition |
| Financial Statements | 4 components | 5 components (includes Statement of Changes in Equity) |

## Standards with No VAS Equivalent

- IAS 20 (Government Grants)
- IAS 41 (Agriculture)
- IFRS 5 (Held-for-Sale)
- IFRS 9 (Financial Instruments)
- IFRS 13 (Fair Value Measurement)
- IFRS 15 (Revenue)
- IFRS 16 (Leases)

## Abstraction Layer Design

### IAccountingPolicy Interface

```csharp
namespace SmeAccounting.Domain.Ports;

public interface IAccountingPolicy
{
    string Name { get; }
    string Version { get; }
    
    // Measurement rules
    MeasurementMethod GetMeasurementMethod(AssetType assetType);
    RevenueRecognitionRule GetRevenueRecognitionRule(TransactionType transactionType);
    LeaseClassificationRule GetLeaseClassificationRule(LeaseTerms terms);
    
    // Valuation
    decimal CalculateDepreciation(FixedAsset asset, DateTimeOffset date);
    decimal CalculateInventoryValue(IReadOnlyList<StockMovement> movements, ValuationMethod method);
    
    // Financial instruments (IFRS only)
    bool SupportsFinancialInstruments { get; }
    RecognitionResult RecognizeFinancialInstrument(FinancialInstrument instrument);
}
```

### Implementations

```csharp
// Current default
public class VasAccountingPolicy : IAccountingPolicy
{
    public string Name => "VAS";
    public string Version => "2005";
    public bool SupportsFinancialInstruments => false;
    // VAS rules: historical cost, no revaluation, operating lease expense
}

// Future implementation
public class IfrsAccountingPolicy : IAccountingPolicy
{
    public string Name => "IFRS";
    public string Version => "2024";
    public bool SupportsFinancialInstruments => true;
    // IFRS rules: fair value, ROU assets, five-step revenue model
}
```

### Policy Selection

```csharp
// Application layer selects policy based on company configuration
public class AccountingPolicyFactory
{
    private readonly IReadOnlyDictionary<string, IAccountingPolicy> _policies;
    
    public IAccountingPolicy GetPolicy(string policyName)
    {
        return _policies.TryGetValue(policyName, out var policy)
            ? policy
            : throw new UnsupportedAccountingPolicyException(policyName);
    }
}
```

## Architecture Implications

1. **Domain model must not be locked to VAS-only measurement rules**
   - Depreciation calculations behind `IAccountingPolicy`
   - Revenue recognition behind `IAccountingPolicy`
   - Inventory valuation behind `IAccountingPolicy`

2. **Infrastructure provides policy implementations**
   - `VasAccountingPolicy` for current VAS compliance
   - `IfrsAccountingPolicy` for future IFRS transition

3. **Application layer selects policy**
   - Company configuration determines which policy to use
   - Policy name stored in company settings

4. **Reporting must support both standards**
   - VAS: 4 financial statements
   - IFRS: 5 financial statements (adds Statement of Changes in Equity)

## Migration Strategy

1. **Phase 1 (Current)**: Implement `VasAccountingPolicy` as default
2. **Phase 2**: Add `IfrsAccountingPolicy` implementation
3. **Phase 3**: Support policy switching per company configuration
4. **Phase 4**: Handle dual reporting during transition period

## Traceability Matrix

| Regulation | Article/Section | Architecture Component | Layer | Test | Status |
|-----------|-----------------|----------------------|-------|------|--------|
| Decision 345 | Phase I | IAccountingPolicy | Domain | PolicyTests | Planned |
| Decision 345 | Phase II | IfrsAccountingPolicy | Infrastructure | PolicyTests | Planned |
| VAS 14 | VAS 14 | Revenue recognition | Domain | RevenueTests | Planned |
| IFRS 15 | IFRS 15 | Five-step model | Domain | RevenueTests | Planned |
| VAS 06 | VAS 06 | Operating lease | Domain | LeaseTests | Planned |
| IFRS 16 | IFRS 16 | ROU asset + lease liability | Domain | LeaseTests | Planned |
