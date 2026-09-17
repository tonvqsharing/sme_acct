using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivatePostingConfigurationCommand(long ConfigId) : IRequest<DeactivatePostingConfigurationResult>;

public record DeactivatePostingConfigurationResult;
