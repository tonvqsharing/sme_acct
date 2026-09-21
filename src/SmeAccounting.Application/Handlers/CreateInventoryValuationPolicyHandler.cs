using MediatR; using SmeAccounting.Application.Commands; using SmeAccounting.Domain.Entities; using SmeAccounting.Domain.Ports;
namespace SmeAccounting.Application.Handlers;
internal sealed class CreateInventoryValuationPolicyHandler(IInventoryValuationPolicyRepository repo, IUnitOfWork uow) : IRequestHandler<CreateInventoryValuationPolicyCommand, CreateInventoryValuationPolicyResult>
{
    public async Task<CreateInventoryValuationPolicyResult> Handle(CreateInventoryValuationPolicyCommand req, CancellationToken ct)
    {
        if (!Enum.TryParse<ValuationMethod>(req.ValuationMethod, true, out var method))
            throw new ArgumentException("Invalid valuation method");
        var p = new InventoryValuationPolicy(req.CompanyId, req.Code, req.Name, method, req.Description);
        await repo.AddAsync(p);
        await uow.SaveChangesAsync(ct);
        return new CreateInventoryValuationPolicyResult(p.Id);
    }
}
