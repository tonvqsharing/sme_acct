using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateCustomerCommand(
    long CompanyId,
    string Code,
    string Name,
    string? TaxCode = null,
    string? Address = null,
    string? Phone = null,
    string? Email = null,
    string? Description = null) : IRequest<CreateCustomerResult>;

public record CreateCustomerResult(long Id);
