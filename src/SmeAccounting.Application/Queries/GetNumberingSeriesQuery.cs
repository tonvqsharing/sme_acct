using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetNumberingSeriesQuery(long SeriesId) : IRequest<DocumentNumberingSeriesDto?>;
