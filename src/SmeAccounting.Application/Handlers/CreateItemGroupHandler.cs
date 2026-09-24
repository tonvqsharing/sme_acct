using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemGroupHandler(IItemGroupRepository repository, IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemGroupCommand, CreateItemGroupResult>
{
    public async Task<CreateItemGroupResult> Handle(CreateItemGroupCommand request, CancellationToken cancellationToken)
    {
        var itemGroup = new ItemGroup(request.CompanyId, request.Code, request.Name, request.Description);
        await repository.AddAsync(itemGroup);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateItemGroupResult(itemGroup.Id);
    }
}