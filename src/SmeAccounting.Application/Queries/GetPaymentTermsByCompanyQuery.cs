using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetPaymentTermsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<PaymentTermDto>>;
