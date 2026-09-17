using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxExemptionReasonCommand(long TaxExemptionReasonId) : IRequest<DeactivateTaxExemptionReasonResult>;

public record DeactivateTaxExemptionReasonResult;
