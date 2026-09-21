using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class PostOpeningBalancesHandler(
    IOpeningBalancePeriodRepository periodRepository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<PostOpeningBalancesCommand, PostOpeningBalancesResult>
{
    public async Task<PostOpeningBalancesResult> Handle(
        PostOpeningBalancesCommand request,
        CancellationToken cancellationToken)
    {
        var period = await periodRepository.GetByIdAsync(request.PeriodId)
            ?? throw new KeyNotFoundException($"Opening balance period {request.PeriodId} not found.");

        period.PostOpeningBalances(request.PostedBy, request.PostedAt);

        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new PostOpeningBalancesResult(true);
    }
}
