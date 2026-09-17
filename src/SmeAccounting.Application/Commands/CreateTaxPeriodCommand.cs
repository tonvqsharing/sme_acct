using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateTaxPeriodCommand(
    long FiscalPeriodId,
    long TaxTypeId,
    FilingFrequency FilingFrequency,
    DateOnly FilingDeadline,
    long CompanyId,
    string? Description = null) : IRequest<CreateTaxPeriodResult>;

public record CreateTaxPeriodResult(long Id);
