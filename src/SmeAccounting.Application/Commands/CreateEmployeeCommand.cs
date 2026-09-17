using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateEmployeeCommand(
    long CompanyId,
    string Code,
    string Name,
    string? EmployeeNumber = null,
    string? TaxCode = null,
    string? Address = null,
    string? Phone = null,
    string? Email = null,
    DateOnly? HireDate = null,
    string? Description = null) : IRequest<CreateEmployeeResult>;

public record CreateEmployeeResult(long Id);
