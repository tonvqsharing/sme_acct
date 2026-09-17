using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxPeriodCommand(long TaxPeriodId) : IRequest<DeactivateTaxPeriodResult>;

public record DeactivateTaxPeriodResult;
