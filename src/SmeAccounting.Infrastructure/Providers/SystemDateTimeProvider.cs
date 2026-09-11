namespace SmeAccounting.Infrastructure.Providers;

using SmeAccounting.SharedKernel;

public sealed class SystemDateTimeProvider : IDateTimeProvider
{
    public DateTime UtcNow => DateTime.UtcNow;
}