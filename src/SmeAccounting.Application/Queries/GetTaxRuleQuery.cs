using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxRuleQuery(long TaxRuleId) : IRequest<TaxRuleDto?>;
