using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetSuppliersByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<SupplierDto>>;
