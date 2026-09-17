using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateTaxTreatmentCommand(
    string Code,
    string Name,
    long TaxTypeId,
    TaxTreatmentType TaxTreatmentType,
    bool InputCreditAllowed,
    long CompanyId,
    string? Description = null) : IRequest<CreateTaxTreatmentResult>;

public record CreateTaxTreatmentResult(long Id);
