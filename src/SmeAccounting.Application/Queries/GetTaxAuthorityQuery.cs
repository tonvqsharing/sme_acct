using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxAuthorityQuery(long TaxAuthorityId) : IRequest<TaxAuthorityDto?>;
