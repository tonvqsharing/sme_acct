using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetUserByExternalIdHandler(IUsersRepository repository)
    : IRequestHandler<GetUserByExternalIdQuery, UserDto?>
{
    public async Task<UserDto?> Handle(GetUserByExternalIdQuery request, CancellationToken cancellationToken)
    {
        var user = await repository.GetByExternalIdAsync(request.ExternalId);
        if (user is null) return null;
        return new UserDto(user.Id, user.ExternalId, user.Email, user.DisplayName, user.UserName, user.IsActive);
    }
}
