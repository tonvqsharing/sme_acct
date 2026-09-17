using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetNumberingSeriesHandler(
    IDocumentNumberingSeriesRepository repository)
    : IRequestHandler<GetNumberingSeriesQuery, DocumentNumberingSeriesDto?>
{
    public async Task<DocumentNumberingSeriesDto?> Handle(
        GetNumberingSeriesQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.SeriesId);
        return entity is null ? null : new DocumentNumberingSeriesDto(
            entity.Id, entity.VoucherTypeId, entity.CompanyId,
            entity.Prefix, entity.NextNumber, entity.PaddingLength,
            entity.IsDefault, entity.IsActive, entity.Description);
    }
}
