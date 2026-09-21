using MediatR;
namespace SmeAccounting.Application.Commands;
public record DeactivateServiceItemCommand(long Id) : IRequest<DeactivateServiceItemResult>;
public record DeactivateServiceItemResult(bool Success);
