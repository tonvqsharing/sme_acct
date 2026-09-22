using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetPaymentMethodQuery(long PaymentMethodId) : IRequest<PaymentMethodDto?>;
