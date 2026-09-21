using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Entities; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class CreateServiceItemHandler(IServiceItemRepository repo, IUnitOfWork uow) : IRequestHandler<CreateServiceItemCommand, CreateServiceItemResult>
{
    public async Task<CreateServiceItemResult> Handle(CreateServiceItemCommand req, CancellationToken ct)
    {
        var s = new ServiceItem(req.CompanyId, req.Code, req.Name, req.UomId, req.Description);
        await repo.AddAsync(s);
        await uow.SaveChangesAsync(ct);
        return new CreateServiceItemResult(s.Id);
    }
}
