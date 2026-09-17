using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateTaxAccountingMappingCommand(
    long TaxTypeId,
    long TaxTreatmentId,
    long AccountId,
    TaxAccountingMappingType MappingType,
    long CompanyId,
    string? Description = null) : IRequest<CreateTaxAccountingMappingResult>;

public record CreateTaxAccountingMappingResult(long Id);
