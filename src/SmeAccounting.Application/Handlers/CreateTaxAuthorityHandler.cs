using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxAuthorityHandler(
    ITaxAuthorityRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxAuthorityCommand, CreateTaxAuthorityResult>
{
    public async Task<CreateTaxAuthorityResult> Handle(
        CreateTaxAuthorityCommand request,
        CancellationToken cancellationToken)
    {
        var taxAuthority = new TaxAuthority(
            request.CompanyId, request.Code, request.Name,
            request.AuthorityLevel, request.Address,
            request.Phone, request.Description);

        await repository.AddAsync(taxAuthority);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxAuthorityResult(taxAuthority.Id);
    }
}
