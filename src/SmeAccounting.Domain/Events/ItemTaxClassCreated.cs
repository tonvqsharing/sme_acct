using SmeAccounting.Domain.Events;

namespace SmeAccounting.Domain.Events;

public sealed class ItemTaxClassCreated : DomainEvent
{
    public long ItemTaxClassId { get; }
    public long CompanyId { get; }

    public ItemTaxClassCreated(long itemTaxClassId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        ItemTaxClassId = itemTaxClassId;
        CompanyId = companyId;
    }
}