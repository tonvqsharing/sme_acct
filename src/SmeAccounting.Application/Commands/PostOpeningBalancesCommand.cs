using MediatR;

namespace SmeAccounting.Application.Commands;

public record PostOpeningBalancesCommand(
    long PeriodId,
    string PostedBy,
    DateTimeOffset PostedAt) : IRequest<PostOpeningBalancesResult>;

public record PostOpeningBalancesResult(bool Success);
