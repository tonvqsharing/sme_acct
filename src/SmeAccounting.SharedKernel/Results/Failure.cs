namespace SmeAccounting.SharedKernel;

public sealed record Failure(string Code, string Description)
{
    public static readonly Failure None = new(string.Empty, string.Empty);
}