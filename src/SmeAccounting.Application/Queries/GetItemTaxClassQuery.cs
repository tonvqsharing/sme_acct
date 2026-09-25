using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemTaxClassQuery(long Id) : IRequest<ItemTaxClassDto?>;

public record GetItemTaxClassesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemTaxClassDto>>;