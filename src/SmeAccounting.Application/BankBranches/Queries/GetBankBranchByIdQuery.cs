using MediatR;
using SmeAccounting.Application.BankBranches.DTOs;

namespace SmeAccounting.Application.BankBranches.Queries;

public record GetBankBranchByIdQuery(long Id) : IRequest<BankBranchDto?>;
