using SmeAccounting.SharedKernel;

namespace SmeAccounting.Infrastructure.Persistence.Entities;

public class AuditLogEntry : BaseEntity, IAuditable
{
    public string EntityName { get; set; } = default!;
    public string EntityId { get; set; } = default!;
    public string Action { get; set; } = default!;
    public Guid? ChangedBy { get; set; }
    public DateTime ChangedAtUtc { get; set; }
    public string? Snapshot { get; set; }
    public DateTime CreatedAtUtc { get; set; }
    public Guid? CreatedBy { get; set; }
    public DateTime? UpdatedAtUtc { get; set; }
    public Guid? UpdatedBy { get; set; }
}
