using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetNumberingSeriesByCompanyHandler(
    IDocumentNumberingSeriesRepository repository)
    : IRequestHandler<GetNumberingSeriesByCompanyQuery, IReadOnlyList<DocumentNumberingSeriesDto>>
{
    public async Task<IReadOnlyList<DocumentNumberingSeriesDto>> Handle(
        GetNumberingSeriesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new DocumentNumberingSeriesDto(
                e.Id, e.VoucherTypeId, e.CompanyId,
                e.Prefix, e.NextNumber, e.PaddingLength,
                e.IsDefault, e.IsActive, e.Description))
            .ToList();
    }
}
