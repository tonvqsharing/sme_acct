using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxAuthorityCommand(long TaxAuthorityId) : IRequest<DeactivateTaxAuthorityResult>;

public record DeactivateTaxAuthorityResult;
