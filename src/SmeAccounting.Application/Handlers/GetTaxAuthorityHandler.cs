using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxAuthorityHandler(
    ITaxAuthorityRepository repository)
    : IRequestHandler<GetTaxAuthorityQuery, TaxAuthorityDto?>
{
    public async Task<TaxAuthorityDto?> Handle(
        GetTaxAuthorityQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxAuthorityId);
        return entity is null ? null : new TaxAuthorityDto(
            entity.Id, entity.Code, entity.Name,
            entity.AuthorityLevel.ToString(),
            entity.CompanyId, entity.IsActive,
            entity.Address, entity.Phone, entity.Description);
    }
}
