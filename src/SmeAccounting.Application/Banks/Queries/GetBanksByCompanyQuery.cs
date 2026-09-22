using MediatR;
using SmeAccounting.Application.Banks.DTOs;

namespace SmeAccounting.Application.Banks.Queries;

public record GetBanksByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<BankDto>>;
