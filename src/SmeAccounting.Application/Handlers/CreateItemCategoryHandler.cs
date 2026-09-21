using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemCategoryHandler(
    IItemCategoryRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemCategoryCommand, CreateItemCategoryResult>
{
    public async Task<CreateItemCategoryResult> Handle(CreateItemCategoryCommand request, CancellationToken cancellationToken)
    {
        var category = new ItemCategory(request.CompanyId, request.Code, request.Name, request.ParentId, request.Description);
        await repository.AddAsync(category);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateItemCategoryResult(category.Id);
    }
}
