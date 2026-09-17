using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetVoucherTypeHandler(
    IVoucherTypeRepository repository)
    : IRequestHandler<GetVoucherTypeQuery, VoucherTypeDto?>
{
    public async Task<VoucherTypeDto?> Handle(
        GetVoucherTypeQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.VoucherTypeId);
        return entity is null ? null : new VoucherTypeDto(
            entity.Id, entity.Code, entity.Name,
            entity.VoucherCategory.ToString(),
            entity.CompanyId, entity.IsActive, entity.Description);
    }
}
