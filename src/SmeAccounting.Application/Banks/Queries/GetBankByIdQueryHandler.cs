using MediatR;
using SmeAccounting.Application.Banks.DTOs;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Banks.Queries;

internal sealed class GetBankByIdQueryHandler(
    IBankRepository repository)
    : IRequestHandler<GetBankByIdQuery, BankDto?>
{
    public async Task<BankDto?> Handle(
        GetBankByIdQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.BankId);
        return entity is null ? null : new BankDto(
            entity.Id,
            entity.CompanyId,
            entity.Code,
            entity.Name,
            entity.IsActive,
            entity.Description);
    }
}
