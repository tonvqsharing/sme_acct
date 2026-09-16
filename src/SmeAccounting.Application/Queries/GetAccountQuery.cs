using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetAccountQuery(long AccountId) : IRequest<AccountDto?>;
