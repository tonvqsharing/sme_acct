using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemCategoryQuery(long Id) : IRequest<ItemCategoryDto?>;

public record GetItemCategoriesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemCategoryDto>>;
