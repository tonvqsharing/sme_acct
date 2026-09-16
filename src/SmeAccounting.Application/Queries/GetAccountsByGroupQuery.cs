using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetAccountsByGroupQuery(long AccountGroupId) : IRequest<IReadOnlyList<AccountDto>>;
