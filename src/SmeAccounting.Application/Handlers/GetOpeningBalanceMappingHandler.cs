using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetOpeningBalanceMappingHandler(
    IOpeningBalanceMappingRepository repository)
    : IRequestHandler<GetOpeningBalanceMappingQuery, OpeningBalanceMappingDto?>
{
    public async Task<OpeningBalanceMappingDto?> Handle(
        GetOpeningBalanceMappingQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.MappingId);
        return entity is null ? null : new OpeningBalanceMappingDto(
            entity.Id, entity.CompanyId, entity.VoucherTypeId,
            entity.DebitAccountId, entity.CreditAccountId,
            entity.IsActive, entity.Description);
    }
}
