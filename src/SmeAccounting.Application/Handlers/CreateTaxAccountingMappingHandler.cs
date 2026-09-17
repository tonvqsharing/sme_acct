using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxAccountingMappingHandler(
    ITaxAccountingMappingRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxAccountingMappingCommand, CreateTaxAccountingMappingResult>
{
    public async Task<CreateTaxAccountingMappingResult> Handle(
        CreateTaxAccountingMappingCommand request,
        CancellationToken cancellationToken)
    {
        var mapping = new TaxAccountingMapping(
            request.CompanyId, request.TaxTypeId,
            request.TaxTreatmentId, request.AccountId,
            request.MappingType, request.Description);

        await repository.AddAsync(mapping);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxAccountingMappingResult(mapping.Id);
    }
}
