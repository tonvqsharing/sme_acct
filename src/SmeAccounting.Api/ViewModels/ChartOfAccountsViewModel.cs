using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Api.ViewModels;

public record ChartOfAccountsViewModel(
    IReadOnlyList<AccountDto> Accounts,
    string? SelectedGroupFilter);
