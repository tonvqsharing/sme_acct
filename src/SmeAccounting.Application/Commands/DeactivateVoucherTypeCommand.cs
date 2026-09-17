using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateVoucherTypeCommand(long VoucherTypeId) : IRequest<DeactivateVoucherTypeResult>;

public record DeactivateVoucherTypeResult;
