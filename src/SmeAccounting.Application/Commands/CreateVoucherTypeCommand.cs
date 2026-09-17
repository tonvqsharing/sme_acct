using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateVoucherTypeCommand(
    string Code,
    string Name,
    VoucherCategory VoucherCategory,
    long CompanyId,
    string? Description = null) : IRequest<CreateVoucherTypeResult>;

public record CreateVoucherTypeResult(long Id);
