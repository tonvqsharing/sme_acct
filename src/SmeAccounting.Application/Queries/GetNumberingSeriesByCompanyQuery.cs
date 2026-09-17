using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetNumberingSeriesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<DocumentNumberingSeriesDto>>;
