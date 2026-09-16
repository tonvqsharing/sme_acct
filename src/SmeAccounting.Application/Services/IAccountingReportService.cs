using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Services;

public interface IAccountingReportService
{
    Task<BalanceSheetDto> GetBalanceSheetAsync(long periodId, CancellationToken ct = default);
    Task<IncomeStatementDto> GetIncomeStatementAsync(long periodId, CancellationToken ct = default);
}
