using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateOpeningBalanceMappingCommand(
    long CompanyId,
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    string? Description = null) : IRequest<CreateOpeningBalanceMappingResult>;

public record CreateOpeningBalanceMappingResult(long Id);
