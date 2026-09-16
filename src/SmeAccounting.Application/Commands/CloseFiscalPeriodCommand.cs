using MediatR;

namespace SmeAccounting.Application.Commands;

public record CloseFiscalPeriodCommand(long PeriodId) : IRequest<CloseFiscalPeriodResult>;

public record CloseFiscalPeriodResult(long PeriodId, DateTimeOffset ClosedAt);
