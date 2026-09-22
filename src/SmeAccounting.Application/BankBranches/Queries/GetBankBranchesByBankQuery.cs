using MediatR;
using SmeAccounting.Application.BankBranches.DTOs;

namespace SmeAccounting.Application.BankBranches.Queries;

public record GetBankBranchesByBankQuery(long BankId) : IRequest<IReadOnlyList<BankBranchDto>>;
