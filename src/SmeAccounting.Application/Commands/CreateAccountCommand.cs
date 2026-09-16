using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateAccountCommand(
    string Code,
    string Name,
    AccountType AccountType,
    long? ParentId,
    long? AccountGroupId) : IRequest<CreateAccountResult>;

public record CreateAccountResult(long Id);
