using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateOpeningBalancePeriodHandler(
    IOpeningBalancePeriodRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateOpeningBalancePeriodCommand, CreateOpeningBalancePeriodResult>
{
    public async Task<CreateOpeningBalancePeriodResult> Handle(
        CreateOpeningBalancePeriodCommand request,
        CancellationToken cancellationToken)
    {
        var period = new OpeningBalancePeriod(
            request.CompanyId,
            request.FiscalPeriodId,
            request.PeriodDate);

        await repository.AddAsync(period);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateOpeningBalancePeriodResult(period.Id);
    }
}
