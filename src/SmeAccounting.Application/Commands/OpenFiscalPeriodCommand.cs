using MediatR;

namespace SmeAccounting.Application.Commands;

public record OpenFiscalPeriodCommand(long YearId, int Month) : IRequest<OpenFiscalPeriodResult>;

public record OpenFiscalPeriodResult(long PeriodId);
