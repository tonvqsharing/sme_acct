using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Identity.Domain;

public class User : BaseEntity
{
    protected User()
    {
    }

    public string DisplayName { get; set; } = default!;

    public string Email { get; set; } = default!;

    public string UserName { get; set; } = default!;

    public long? BranchId { get; set; }

    public bool IsEnabled { get; set; } = true;

    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;

    public DateTime? LastLoginAtUtc { get; set; }

    public string? PasswordHash { get; set; }

    public int FailedLoginAttempts { get; set; }

    public DateTimeOffset? LockedUntilUtc { get; set; }

    public bool IsLockedOut => LockedUntilUtc.HasValue && LockedUntilUtc.Value > DateTime.UtcNow;

    public void RecordSuccessfulLogin(IDateTimeProvider clock)
    {
        LastLoginAtUtc = clock.UtcNow;
        FailedLoginAttempts = 0;
        LockedUntilUtc = null;
    }

    public void RecordFailedLogin(IDateTimeProvider clock, int maxAttempts, TimeSpan lockoutDuration)
    {
        FailedLoginAttempts++;

        if (FailedLoginAttempts >= maxAttempts)
        {
            LockedUntilUtc = clock.UtcNow.Add(lockoutDuration);
        }
    }

    public void Lock(DateTimeOffset until)
    {
        LockedUntilUtc = until;
    }

    public void Unlock()
    {
        LockedUntilUtc = null;
        FailedLoginAttempts = 0;
    }

    public void SetPasswordHash(string hash)
    {
        PasswordHash = hash;
    }

    public void Deactivate()
    {
        IsEnabled = false;
    }

    public void Activate()
    {
        IsEnabled = true;
    }
}
