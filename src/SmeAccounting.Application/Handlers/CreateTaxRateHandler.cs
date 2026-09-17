using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxRateHandler(
    ITaxRateRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxRateCommand, CreateTaxRateResult>
{
    public async Task<CreateTaxRateResult> Handle(
        CreateTaxRateCommand request,
        CancellationToken cancellationToken)
    {
        var taxRate = new TaxRate(
            request.CompanyId, request.TaxTypeId,
            request.RateValue, request.RateName,
            request.EffectiveFrom, request.EffectiveTo,
            request.Description);

        await repository.AddAsync(taxRate);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxRateResult(taxRate.Id);
    }
}
