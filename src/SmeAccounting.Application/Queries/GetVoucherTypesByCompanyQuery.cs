using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetVoucherTypesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<VoucherTypeDto>>;
