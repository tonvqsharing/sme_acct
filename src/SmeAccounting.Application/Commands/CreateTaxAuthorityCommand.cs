using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateTaxAuthorityCommand(
    string Code,
    string Name,
    TaxAuthorityLevel AuthorityLevel,
    long CompanyId,
    string? Address = null,
    string? Phone = null,
    string? Description = null) : IRequest<CreateTaxAuthorityResult>;

public record CreateTaxAuthorityResult(long Id);
