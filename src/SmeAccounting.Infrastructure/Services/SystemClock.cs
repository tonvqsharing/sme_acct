using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Infrastructure.Services;

public class SystemClock : IClock
{
    public DateTimeOffset Now => DateTimeOffset.UtcNow;
}
