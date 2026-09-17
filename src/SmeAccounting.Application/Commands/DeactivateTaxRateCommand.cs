using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxRateCommand(long TaxRateId) : IRequest<DeactivateTaxRateResult>;

public record DeactivateTaxRateResult;
