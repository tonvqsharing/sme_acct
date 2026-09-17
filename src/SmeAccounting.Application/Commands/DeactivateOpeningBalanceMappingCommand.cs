using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateOpeningBalanceMappingCommand(long MappingId) : IRequest<DeactivateOpeningBalanceMappingResult>;

public record DeactivateOpeningBalanceMappingResult;
