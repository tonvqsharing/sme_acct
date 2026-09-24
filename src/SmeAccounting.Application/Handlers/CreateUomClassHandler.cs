using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateUomClassHandler(
    IUomClassRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateUomClassCommand, CreateUomClassResult>
{
    public async Task<CreateUomClassResult> Handle(CreateUomClassCommand request, CancellationToken cancellationToken)
    {
        var uomClass = new UomClass(request.CompanyId, request.Code, request.Name, request.Description);
        await repository.AddAsync(uomClass);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateUomClassResult(uomClass.Id);
    }
}