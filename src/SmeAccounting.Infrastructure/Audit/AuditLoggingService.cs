using Microsoft.Extensions.Logging;
using SmeAccounting.Infrastructure.Persistence;
using SmeAccounting.Infrastructure.Persistence.Entities;

namespace SmeAccounting.Infrastructure.Audit;

public interface IAuditLoggingService
{
    Task LogAsync(string entityName, string entityId, string action, object? snapshot = null, Guid? userId = null);
}

public class AuditLoggingService : IAuditLoggingService
{
    private readonly SmeAccountingDbContext _dbContext;
    private readonly ILogger<AuditLoggingService> _logger;
    
    public AuditLoggingService(SmeAccountingDbContext dbContext, ILogger<AuditLoggingService> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }
    
    public async Task LogAsync(string entityName, string entityId, string action, object? snapshot = null, Guid? userId = null)
    {
        var entry = new AuditLogEntry
        {
            EntityName = entityName,
            EntityId = entityId,
            Action = action,
            ChangedBy = userId,
            ChangedAtUtc = DateTime.UtcNow,
            Snapshot = snapshot?.ToString()
        };
        
        _dbContext.AuditLogEntries.Add(entry);
        await _dbContext.SaveChangesAsync();
        
        _logger.LogInformation("Audit: {Action} on {EntityName} {EntityId} by {UserId}", 
            action, entityName, entityId, userId);
    }
}
