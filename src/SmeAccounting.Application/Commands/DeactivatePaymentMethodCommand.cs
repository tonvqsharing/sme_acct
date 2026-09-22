using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivatePaymentMethodCommand(long PaymentMethodId) : IRequest<DeactivatePaymentMethodResult>;

public record DeactivatePaymentMethodResult;
