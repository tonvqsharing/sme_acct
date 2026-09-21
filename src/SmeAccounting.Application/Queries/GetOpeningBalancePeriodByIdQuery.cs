using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetOpeningBalancePeriodByIdQuery(long PeriodId) : IRequest<OpeningBalancePeriodDto?>;
