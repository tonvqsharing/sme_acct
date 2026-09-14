namespace SmeAccounting.Infrastructure.Options;

public class SecurityOptions
{
    public const string SectionName = "Security";
    public int LockoutMaxAttempts { get; set; } = 5;
    public int LockoutDurationMinutes { get; set; } = 15;
    public string DataProtectionPath { get; set; } = "./dataprotection-keys";
}
