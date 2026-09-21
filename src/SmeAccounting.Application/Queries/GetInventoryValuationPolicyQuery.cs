using MediatR; using SmeAccounting.Application.DTOs;
namespace SmeAccounting.Application.Queries;
public record GetInventoryValuationPolicyQuery(long Id) : IRequest<InventoryValuationPolicyDto?>;
public record GetInventoryValuationPoliciesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<InventoryValuationPolicyDto>>;
