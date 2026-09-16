using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Infrastructure.Services;

public class AuditLogger : IAuditLogger
{
    public async Task LogAsync(string action, string entity, long entityId, string details)
    {
        Console.WriteLine($"[AUDIT] {action} on {entity}:{entityId} — {details}");
        await Task.CompletedTask;
    }
}
