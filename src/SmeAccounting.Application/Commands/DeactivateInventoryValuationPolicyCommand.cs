using MediatR;
namespace SmeAccounting.Application.Commands;
public record DeactivateInventoryValuationPolicyCommand(long Id) : IRequest<DeactivateInventoryValuationPolicyResult>;
public record DeactivateInventoryValuationPolicyResult(bool Success);
