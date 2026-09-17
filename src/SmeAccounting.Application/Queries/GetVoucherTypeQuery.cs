using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetVoucherTypeQuery(long VoucherTypeId) : IRequest<VoucherTypeDto?>;
