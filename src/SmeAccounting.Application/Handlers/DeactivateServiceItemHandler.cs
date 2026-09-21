using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class DeactivateServiceItemHandler(IServiceItemRepository repo, IUnitOfWork uow) : IRequestHandler<DeactivateServiceItemCommand, DeactivateServiceItemResult>
{
    public async Task<DeactivateServiceItemResult> Handle(DeactivateServiceItemCommand req, CancellationToken ct)
    {
        var s = await repo.GetByIdAsync(req.Id);
        if (s == null) return new DeactivateServiceItemResult(false);
        s.Deactivate();
        await uow.SaveChangesAsync(ct);
        return new DeactivateServiceItemResult(true);
    }
}
