using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateOpeningBalanceMappingHandler(
    IOpeningBalanceMappingRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateOpeningBalanceMappingCommand, CreateOpeningBalanceMappingResult>
{
    public async Task<CreateOpeningBalanceMappingResult> Handle(
        CreateOpeningBalanceMappingCommand request,
        CancellationToken cancellationToken)
    {
        var mapping = new OpeningBalanceMapping(
            request.CompanyId, request.VoucherTypeId,
            request.DebitAccountId, request.CreditAccountId,
            request.Description);

        await repository.AddAsync(mapping);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateOpeningBalanceMappingResult(mapping.Id);
    }
}
