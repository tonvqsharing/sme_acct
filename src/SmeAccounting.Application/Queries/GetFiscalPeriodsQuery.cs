using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetFiscalPeriodsQuery(long? YearId) : IRequest<IReadOnlyList<FiscalPeriodDto>>;
