using MediatR;
using SmeAccounting.Application.BankBranches.DTOs;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.BankBranches.Queries;

internal sealed class GetBankBranchesByBankQueryHandler(
    IBankBranchRepository repository)
    : IRequestHandler<GetBankBranchesByBankQuery, IReadOnlyList<BankBranchDto>>
{
    public async Task<IReadOnlyList<BankBranchDto>> Handle(
        GetBankBranchesByBankQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByBankAsync(request.BankId);
        return entities.Select(e => new BankBranchDto(
            e.Id,
            e.CompanyId,
            e.BankId,
            e.Code,
            e.Name,
            e.IsActive,
            e.Description)).ToList();
    }
}
