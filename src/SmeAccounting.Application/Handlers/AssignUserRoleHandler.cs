using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class AssignUserRoleHandler(
    IUserRoleRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<AssignUserRoleCommand, AssignUserRoleResult>
{
    public async Task<AssignUserRoleResult> Handle(AssignUserRoleCommand request, CancellationToken cancellationToken)
    {
        var userRole = new UserRole(request.UserId, request.RoleId, request.CompanyId);
        await repository.AddAsync(userRole);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new AssignUserRoleResult(userRole.Id);
    }
}
