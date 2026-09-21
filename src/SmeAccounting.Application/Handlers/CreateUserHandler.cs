using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateUserHandler(
    IUsersRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateUserCommand, CreateUserResult>
{
    public async Task<CreateUserResult> Handle(CreateUserCommand request, CancellationToken cancellationToken)
    {
        var user = new User(request.ExternalId, request.Email, request.DisplayName, request.UserName);
        await repository.AddAsync(user);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateUserResult(user.Id);
    }
}
