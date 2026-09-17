using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxTypeHandler(
    ITaxTypeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxTypeCommand, CreateTaxTypeResult>
{
    public async Task<CreateTaxTypeResult> Handle(
        CreateTaxTypeCommand request,
        CancellationToken cancellationToken)
    {
        var taxType = new TaxType(
            request.CompanyId, request.Code, request.Name,
            request.TaxCategory, request.Description);

        await repository.AddAsync(taxType);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxTypeResult(taxType.Id);
    }
}
