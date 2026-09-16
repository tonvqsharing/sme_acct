namespace SmeAccounting.Application.DTOs;

public record BalanceSheetDto(
    IReadOnlyList<AccountGroupTotal> Assets,
    IReadOnlyList<AccountGroupTotal> Liabilities,
    IReadOnlyList<AccountGroupTotal> Equity);

public record AccountGroupTotal(string GroupName, decimal Total, string Currency);
