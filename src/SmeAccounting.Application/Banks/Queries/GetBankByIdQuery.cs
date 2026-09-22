using MediatR;
using SmeAccounting.Application.Banks.DTOs;

namespace SmeAccounting.Application.Banks.Queries;

public record GetBankByIdQuery(long BankId) : IRequest<BankDto?>;
