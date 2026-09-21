using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateUserCommand(
    string ExternalId,
    string Email,
    string DisplayName,
    string? UserName = null) : IRequest<CreateUserResult>;

public record CreateUserResult(long Id);
