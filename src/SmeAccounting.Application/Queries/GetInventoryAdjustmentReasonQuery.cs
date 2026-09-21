using MediatR; using SmeAccounting.Application.DTOs;
namespace SmeAccounting.Application.Queries;
public record GetInventoryAdjustmentReasonQuery(long Id) : IRequest<InventoryAdjustmentReasonDto?>;
public record GetInventoryAdjustmentReasonsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<InventoryAdjustmentReasonDto>>;
