using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class ResetNumberingSeriesHandler(
    IDocumentNumberingSeriesRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<ResetNumberingSeriesCommand, ResetNumberingSeriesResult>
{
    public async Task<ResetNumberingSeriesResult> Handle(
        ResetNumberingSeriesCommand request,
        CancellationToken cancellationToken)
    {
        var series = await repository.GetByIdAsync(request.SeriesId);
        if (series is null)
            throw new InvalidOperationException($"Numbering series with ID {request.SeriesId} not found.");

        series.Reset(request.StartFrom);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new ResetNumberingSeriesResult();
    }
}
