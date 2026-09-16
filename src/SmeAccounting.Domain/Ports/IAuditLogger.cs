namespace SmeAccounting.Domain.Ports;

public interface IAuditLogger
{
    Task LogAsync(string action, string entity, long entityId, string details);
}
