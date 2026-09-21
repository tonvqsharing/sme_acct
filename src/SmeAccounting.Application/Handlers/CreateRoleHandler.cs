using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateRoleHandler(
    IRoleRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateRoleCommand, CreateRoleResult>
{
    public async Task<CreateRoleResult> Handle(CreateRoleCommand request, CancellationToken cancellationToken)
    {
        var role = new Role(request.CompanyId, request.Code, request.Name, request.Description);
        await repository.AddAsync(role);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateRoleResult(role.Id);
    }
}
