using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class PostingConfiguration : BaseEntity
{
    public long VoucherTypeId { get; private set; }
    public long DebitAccountId { get; private set; }
    public long CreditAccountId { get; private set; }
    public long CompanyId { get; private set; }
    public long? TransactionReasonId { get; private set; }
    public int DisplayOrder { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private PostingConfiguration() { }

    public PostingConfiguration(
        long companyId, long voucherTypeId, long debitAccountId, long creditAccountId,
        long? transactionReasonId = null, int displayOrder = 0, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (voucherTypeId <= 0)
            throw new DomainException("VoucherTypeId must be greater than zero.");
        if (debitAccountId <= 0)
            throw new DomainException("DebitAccountId must be greater than zero.");
        if (creditAccountId <= 0)
            throw new DomainException("CreditAccountId must be greater than zero.");
        if (debitAccountId == creditAccountId)
            throw new DomainException("Debit and credit accounts must be different.");
        if (transactionReasonId.HasValue && transactionReasonId <= 0)
            throw new DomainException("TransactionReasonId must be greater than zero when specified.");

        CompanyId = companyId;
        VoucherTypeId = voucherTypeId;
        DebitAccountId = debitAccountId;
        CreditAccountId = creditAccountId;
        TransactionReasonId = transactionReasonId;
        DisplayOrder = displayOrder;
        Description = description;
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
