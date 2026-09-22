using MediatR;
using SmeAccounting.Application.BankBranches.DTOs;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.BankBranches.Queries;

internal sealed class GetBankBranchByIdQueryHandler(
    IBankBranchRepository repository)
    : IRequestHandler<GetBankBranchByIdQuery, BankBranchDto?>
{
    public async Task<BankBranchDto?> Handle(
        GetBankBranchByIdQuery request,
        CancellationToken cancellationToken)
    {
        var branch = await repository.GetByIdAsync(request.Id);
        if (branch is null) return null;

        return new BankBranchDto(
            branch.Id,
            branch.CompanyId,
            branch.BankId,
            branch.Code,
            branch.Name,
            branch.IsActive,
            branch.Description);
    }
}
