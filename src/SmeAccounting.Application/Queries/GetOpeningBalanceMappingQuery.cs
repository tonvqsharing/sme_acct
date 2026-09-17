using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetOpeningBalanceMappingQuery(long MappingId) : IRequest<OpeningBalanceMappingDto?>;
