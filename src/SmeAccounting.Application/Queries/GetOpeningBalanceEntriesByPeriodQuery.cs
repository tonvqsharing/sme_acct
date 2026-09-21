using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetOpeningBalanceEntriesByPeriodQuery(long PeriodId) : IRequest<IReadOnlyList<OpeningBalanceEntryDto>>;
