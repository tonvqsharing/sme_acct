using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreatePaymentTermCommand(
    long CompanyId,
    string Code,
    string Name,
    PaymentTermType PaymentTermType,
    int? Days = null,
    string? Description = null) : IRequest<CreatePaymentTermResult>;

public record CreatePaymentTermResult(long Id);
