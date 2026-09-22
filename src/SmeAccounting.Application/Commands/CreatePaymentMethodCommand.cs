using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreatePaymentMethodCommand(
    long CompanyId,
    string Code,
    string Name,
    PaymentMethodCategory Category,
    bool RequiresBankAccount = false,
    string? Description = null) : IRequest<CreatePaymentMethodResult>;

public record CreatePaymentMethodResult(long Id);
