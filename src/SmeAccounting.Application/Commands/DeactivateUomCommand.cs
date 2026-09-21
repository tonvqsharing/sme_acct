using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateUomCommand(long Id) : IRequest<DeactivateUomResult>;

public record DeactivateUomResult(bool Success);
