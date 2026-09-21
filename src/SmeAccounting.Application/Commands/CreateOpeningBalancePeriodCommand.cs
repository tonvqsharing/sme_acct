using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateOpeningBalancePeriodCommand(
    long CompanyId,
    long FiscalPeriodId,
    DateOnly PeriodDate) : IRequest<CreateOpeningBalancePeriodResult>;

public record CreateOpeningBalancePeriodResult(long Id);
