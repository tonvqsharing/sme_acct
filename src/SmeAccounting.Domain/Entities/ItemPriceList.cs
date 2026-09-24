using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class ItemPriceList : BaseEntity
{
    public long CompanyId { get; private set; }
    public long PriceListId { get; private set; }
    public long ItemId { get; private set; }
    public decimal UnitPrice { get; private set; }
    public string CurrencyCode { get; private set; } = string.Empty;
    public DateOnly EffectiveFrom { get; private set; }
    public DateOnly? EffectiveTo { get; private set; }
    public bool IsActive { get; private set; } = true;

    private ItemPriceList() { }

    public ItemPriceList(
        long companyId,
        long priceListId,
        long itemId,
        decimal unitPrice,
        string currencyCode,
        DateOnly effectiveFrom,
        DateOnly? effectiveTo = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (priceListId <= 0)
            throw new DomainException("PriceListId must be greater than zero.");
        if (itemId <= 0)
            throw new DomainException("ItemId must be greater than zero.");
        if (unitPrice < 0)
            throw new DomainException("UnitPrice must be greater than or equal to zero.");
        if (string.IsNullOrWhiteSpace(currencyCode))
            throw new DomainException("CurrencyCode is required.");
        if (currencyCode.Length != 3)
            throw new DomainException("CurrencyCode must be exactly 3 characters.");
        if (effectiveTo.HasValue && effectiveTo.Value < effectiveFrom)
            throw new DomainException("EffectiveTo must be null or on/after EffectiveFrom.");

        CompanyId = companyId;
        PriceListId = priceListId;
        ItemId = itemId;
        UnitPrice = unitPrice;
        CurrencyCode = currencyCode.ToUpperInvariant();
        EffectiveFrom = effectiveFrom;
        EffectiveTo = effectiveTo;

        AddDomainEvent(new ItemPriceListCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}