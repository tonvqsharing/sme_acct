using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateTaxRateCommand(
    long TaxTypeId,
    decimal RateValue,
    string RateName,
    DateOnly EffectiveFrom,
    long CompanyId,
    DateOnly? EffectiveTo = null,
    string? Description = null) : IRequest<CreateTaxRateResult>;

public record CreateTaxRateResult(long Id);
