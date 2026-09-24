using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateUomClassCommand(long Id) : IRequest<DeactivateUomClassResult>;

public record DeactivateUomClassResult;