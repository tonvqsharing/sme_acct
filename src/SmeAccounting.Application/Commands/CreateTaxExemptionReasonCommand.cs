using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateTaxExemptionReasonCommand(
    long TaxTypeId,
    string Code,
    string Name,
    string LegalBasis,
    long CompanyId,
    string? Description = null) : IRequest<CreateTaxExemptionReasonResult>;

public record CreateTaxExemptionReasonResult(long Id);
