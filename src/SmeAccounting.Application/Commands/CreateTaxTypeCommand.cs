using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateTaxTypeCommand(
    string Code,
    string Name,
    TaxCategory TaxCategory,
    long CompanyId,
    string? Description = null) : IRequest<CreateTaxTypeResult>;

public record CreateTaxTypeResult(long Id);
