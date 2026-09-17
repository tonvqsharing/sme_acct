using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateDocumentNumberingSeriesHandler(
    IDocumentNumberingSeriesRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateDocumentNumberingSeriesCommand, CreateDocumentNumberingSeriesResult>
{
    public async Task<CreateDocumentNumberingSeriesResult> Handle(
        CreateDocumentNumberingSeriesCommand request,
        CancellationToken cancellationToken)
    {
        var series = new DocumentNumberingSeries(
            request.CompanyId, request.VoucherTypeId, request.Prefix,
            request.PaddingLength, request.IsDefault, request.Description);

        await repository.AddAsync(series);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateDocumentNumberingSeriesResult(series.Id);
    }
}
