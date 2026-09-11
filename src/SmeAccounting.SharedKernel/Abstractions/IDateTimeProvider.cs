namespace SmeAccounting.SharedKernel;

public interface IDateTimeProvider
{
    DateTime UtcNow { get; }
}