using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class User : BaseEntity
{
    public string ExternalId { get; private set; } = string.Empty;
    public string Email { get; private set; } = string.Empty;
    public string DisplayName { get; private set; } = string.Empty;
    public string? UserName { get; private set; }
    public bool IsActive { get; private set; } = true;

    private User() { }

    public User(string externalId, string email, string displayName, string? userName = null)
    {
        if (string.IsNullOrWhiteSpace(externalId))
            throw new DomainException("ExternalId is required.");
        if (string.IsNullOrWhiteSpace(email))
            throw new DomainException("Email is required.");
        if (string.IsNullOrWhiteSpace(displayName))
            throw new DomainException("DisplayName is required.");

        ExternalId = externalId.Trim();
        Email = email.Trim().ToLowerInvariant();
        DisplayName = displayName;
        UserName = userName;

        AddDomainEvent(new UserCreated(Id, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
