using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxRuleCommand(long TaxRuleId) : IRequest<DeactivateTaxRuleResult>;

public record DeactivateTaxRuleResult;
