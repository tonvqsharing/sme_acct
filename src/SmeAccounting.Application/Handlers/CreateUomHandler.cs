using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateUomHandler(
    IUomRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateUomCommand, CreateUomResult>
{
    public async Task<CreateUomResult> Handle(CreateUomCommand request, CancellationToken cancellationToken)
    {
        var uom = new Uom(request.CompanyId, request.Code, request.Name, request.Symbol, request.Description);
        await repository.AddAsync(uom);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateUomResult(uom.Id);
    }
}
