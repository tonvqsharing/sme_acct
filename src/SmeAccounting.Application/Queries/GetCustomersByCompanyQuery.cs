using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetCustomersByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<CustomerDto>>;
