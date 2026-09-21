using MediatR;
namespace SmeAccounting.Application.Commands;
public record CreateInventoryValuationPolicyCommand(long CompanyId, string Code, string Name, string ValuationMethod, string? Description = null) : IRequest<CreateInventoryValuationPolicyResult>;
public record CreateInventoryValuationPolicyResult(long Id);
