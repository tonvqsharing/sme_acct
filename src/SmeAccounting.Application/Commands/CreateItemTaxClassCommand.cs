using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateItemTaxClassCommand(
    long CompanyId,
    long ItemId,
    long TaxTypeId,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo = null)
    : IRequest<CreateItemTaxClassResult>;

public record CreateItemTaxClassResult(long Id);