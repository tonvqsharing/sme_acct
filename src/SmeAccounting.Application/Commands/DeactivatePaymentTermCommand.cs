using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivatePaymentTermCommand(long PaymentTermId) : IRequest<DeactivatePaymentTermResult>;

public record DeactivatePaymentTermResult;
