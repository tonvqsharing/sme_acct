using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxTypeCommand(long TaxTypeId) : IRequest<DeactivateTaxTypeResult>;

public record DeactivateTaxTypeResult;
