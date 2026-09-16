using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateAccountCommand(
    string Code,
    string Name,
    AccountType AccountType,
    long CompanyId,
    NormalBalance NormalBalance,
    long? ParentId,
    long? AccountGroupId,
    string? Description = null) : IRequest<CreateAccountResult>;

public record CreateAccountResult(long Id);
