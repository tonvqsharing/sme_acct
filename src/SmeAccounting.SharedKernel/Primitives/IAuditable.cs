namespace SmeAccounting.SharedKernel;

public interface IAuditable
{
    DateTime CreatedAtUtc { get; set; }

    Guid? CreatedBy { get; set; }

    DateTime? UpdatedAtUtc { get; set; }

    Guid? UpdatedBy { get; set; }
}