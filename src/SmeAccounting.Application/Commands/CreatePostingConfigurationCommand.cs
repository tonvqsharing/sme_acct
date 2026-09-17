using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreatePostingConfigurationCommand(
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    long CompanyId,
    long? TransactionReasonId,
    string? Description = null) : IRequest<CreatePostingConfigurationResult>;

public record CreatePostingConfigurationResult(long Id);
