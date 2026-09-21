using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemCommand(long Id) : IRequest<DeactivateItemResult>;

public record DeactivateItemResult(bool Success);
