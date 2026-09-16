using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetIncomeStatementQuery(long PeriodId) : IRequest<IncomeStatementDto>;
