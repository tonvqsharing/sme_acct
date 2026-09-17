using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetCustomerQuery(long CustomerId) : IRequest<CustomerDto?>;
