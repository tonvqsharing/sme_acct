using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetBalanceSheetQuery(long PeriodId) : IRequest<BalanceSheetDto>;
