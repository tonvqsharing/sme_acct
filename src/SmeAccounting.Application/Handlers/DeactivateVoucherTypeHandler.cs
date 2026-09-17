using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateVoucherTypeHandler(
    IVoucherTypeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateVoucherTypeCommand, DeactivateVoucherTypeResult>
{
    public async Task<DeactivateVoucherTypeResult> Handle(
        DeactivateVoucherTypeCommand request,
        CancellationToken cancellationToken)
    {
        var voucherType = await repository.GetByIdAsync(request.VoucherTypeId);
        if (voucherType is null)
            throw new InvalidOperationException($"Voucher type with ID {request.VoucherTypeId} not found.");

        voucherType.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateVoucherTypeResult();
    }
}
