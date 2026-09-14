namespace SmeAccounting.Infrastructure.Options;

public class SerilogOptions
{
    public const string SectionName = "Serilog";
    public string MinimumLevel { get; set; } = "Information";
}
