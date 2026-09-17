using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class DocumentNumberingSeries : BaseEntity
{
    public long VoucherTypeId { get; private set; }
    public long CompanyId { get; private set; }
    public string Prefix { get; private set; } = string.Empty;
    public int NextNumber { get; private set; } = 1;
    public int PaddingLength { get; private set; } = 6;
    public bool IsDefault { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private DocumentNumberingSeries() { }

    public DocumentNumberingSeries(
        long companyId, long voucherTypeId, string prefix,
        int paddingLength = 6, bool isDefault = false, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (voucherTypeId <= 0)
            throw new DomainException("VoucherTypeId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(prefix))
            throw new DomainException("Prefix is required.");
        if (paddingLength < 1 || paddingLength > 10)
            throw new DomainException("PaddingLength must be between 1 and 10.");

        CompanyId = companyId;
        VoucherTypeId = voucherTypeId;
        Prefix = prefix;
        PaddingLength = paddingLength;
        IsDefault = isDefault;
        Description = description;
    }

    public void Increment()
    {
        NextNumber++;
    }

    public void Reset(int startFrom)
    {
        if (startFrom < 1)
            throw new DomainException("StartFrom must be greater than zero.");
        NextNumber = startFrom;
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
