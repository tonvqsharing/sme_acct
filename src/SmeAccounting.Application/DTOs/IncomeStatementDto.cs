namespace SmeAccounting.Application.DTOs;

public record IncomeStatementDto(
    IReadOnlyList<AccountGroupTotal> Revenue,
    IReadOnlyList<AccountGroupTotal> Expenses,
    decimal NetIncome,
    string Currency);
