using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemReorderLevelCommand(long Id) : IRequest<DeactivateItemReorderLevelResult>;

public record DeactivateItemReorderLevelResult(bool Success);
