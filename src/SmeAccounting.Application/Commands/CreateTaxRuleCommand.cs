using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateTaxRuleCommand(
    long TaxTypeId,
    long? TaxRateId,
    long TaxTreatmentId,
    string Code,
    string Name,
    string LegalReference,
    DateOnly EffectiveFrom,
    long CompanyId,
    DateOnly? EffectiveTo = null,
    string? Conditions = null,
    string? Description = null) : IRequest<CreateTaxRuleResult>;

public record CreateTaxRuleResult(long Id);
