using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetEmployeesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<EmployeeDto>>;
