using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemTaxClassCommand(long Id) : IRequest<DeactivateItemTaxClassResult>;

public record DeactivateItemTaxClassResult(bool Success);