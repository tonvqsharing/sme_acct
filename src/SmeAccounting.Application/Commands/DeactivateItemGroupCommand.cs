using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemGroupCommand(long Id) : IRequest<DeactivateItemGroupResult>;

public record DeactivateItemGroupResult(bool Success);