using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetUserByExternalIdQuery(string ExternalId) : IRequest<UserDto?>;
