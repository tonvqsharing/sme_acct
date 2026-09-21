namespace SmeAccounting.Domain.Events;

public class CompanySettingCreated : DomainEvent
{
    public long SettingId { get; }
    public long CompanyId { get; }

    public CompanySettingCreated(long settingId, long companyId, DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        SettingId = settingId;
        CompanyId = companyId;
    }
}
