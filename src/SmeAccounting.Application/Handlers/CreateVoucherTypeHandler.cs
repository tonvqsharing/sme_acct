using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateVoucherTypeHandler(
    IVoucherTypeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateVoucherTypeCommand, CreateVoucherTypeResult>
{
    public async Task<CreateVoucherTypeResult> Handle(
        CreateVoucherTypeCommand request,
        CancellationToken cancellationToken)
    {
        var voucherType = new VoucherType(
            request.CompanyId, request.Code, request.Name,
            request.VoucherCategory, request.Description);

        await repository.AddAsync(voucherType);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateVoucherTypeResult(voucherType.Id);
    }
}
