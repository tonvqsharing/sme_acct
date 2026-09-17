using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxAccountingMappingCommand(long TaxAccountingMappingId) : IRequest<DeactivateTaxAccountingMappingResult>;

public record DeactivateTaxAccountingMappingResult;
