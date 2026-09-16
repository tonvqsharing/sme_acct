namespace SmeAccounting.Domain.Ports;

public interface IClock
{
    DateTimeOffset Now { get; }
}
