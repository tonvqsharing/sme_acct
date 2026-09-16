using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeprecateAccountCommand(long AccountId) : IRequest<DeprecateAccountResult>;

public record DeprecateAccountResult(long AccountId);
