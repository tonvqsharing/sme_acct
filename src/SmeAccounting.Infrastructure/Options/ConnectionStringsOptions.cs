namespace SmeAccounting.Infrastructure.Options;

public class ConnectionStringsOptions
{
    public const string SectionName = "ConnectionStrings";
    public string DefaultConnection { get; set; } = default!;
}
