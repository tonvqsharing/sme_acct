using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateTransactionReasonCommand(
    string Code,
    string Name,
    long VoucherTypeId,
    long CompanyId,
    string? Description = null) : IRequest<CreateTransactionReasonResult>;

public record CreateTransactionReasonResult(long Id);
