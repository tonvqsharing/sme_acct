using MediatR;

namespace SmeAccounting.Application.Banks.Commands;

public record CreateBankCommand(
    long CompanyId,
    string Code,
    string Name,
    string? Description = null) : IRequest<CreateBankResult>;

public record CreateBankResult(long Id);
