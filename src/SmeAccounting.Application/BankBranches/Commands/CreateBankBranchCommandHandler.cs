using MediatR;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.BankBranches.Commands;

internal sealed class CreateBankBranchCommandHandler(
    IBankBranchRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateBankBranchCommand, CreateBankBranchResult>
{
    public async Task<CreateBankBranchResult> Handle(
        CreateBankBranchCommand request,
        CancellationToken cancellationToken)
    {
        var branch = new BankBranch(
            request.CompanyId,
            request.BankId,
            request.Code,
            request.Name,
            request.Description);

        await repository.AddAsync(branch);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateBankBranchResult(branch.Id);
    }
}
