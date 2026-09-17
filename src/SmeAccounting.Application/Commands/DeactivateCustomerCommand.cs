using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateCustomerCommand(long CustomerId) : IRequest<DeactivateCustomerResult>;

public record DeactivateCustomerResult;
