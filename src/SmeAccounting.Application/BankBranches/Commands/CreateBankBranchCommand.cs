using MediatR;

namespace SmeAccounting.Application.BankBranches.Commands;

public record CreateBankBranchCommand(
    long CompanyId,
    long BankId,
    string Code,
    string Name,
    string? Description = null) : IRequest<CreateBankBranchResult>;

public record CreateBankBranchResult(long Id);
