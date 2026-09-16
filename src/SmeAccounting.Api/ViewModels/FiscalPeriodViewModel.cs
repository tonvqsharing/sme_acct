using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Api.ViewModels;

public record FiscalPeriodViewModel(
    IReadOnlyList<FiscalPeriodDto> Periods);
