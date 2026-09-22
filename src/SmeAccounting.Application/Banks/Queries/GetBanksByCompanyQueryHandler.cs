using MediatR;
using SmeAccounting.Application.Banks.DTOs;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Banks.Queries;

internal sealed class GetBanksByCompanyQueryHandler(
    IBankRepository repository)
    : IRequestHandler<GetBanksByCompanyQuery, IReadOnlyList<BankDto>>
{
    public async Task<IReadOnlyList<BankDto>> Handle(
        GetBanksByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities.Select(e => new BankDto(
            e.Id,
            e.CompanyId,
            e.Code,
            e.Name,
            e.IsActive,
            e.Description)).ToList();
    }
}
