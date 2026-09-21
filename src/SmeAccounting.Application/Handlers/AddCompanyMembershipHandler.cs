using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class AddCompanyMembershipHandler(
    ICompanyMembershipRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<AddCompanyMembershipCommand, AddCompanyMembershipResult>
{
    public async Task<AddCompanyMembershipResult> Handle(AddCompanyMembershipCommand request, CancellationToken cancellationToken)
    {
        var membership = new CompanyMembership(request.UserId, request.CompanyId);
        await repository.AddAsync(membership);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new AddCompanyMembershipResult(membership.Id);
    }
}
