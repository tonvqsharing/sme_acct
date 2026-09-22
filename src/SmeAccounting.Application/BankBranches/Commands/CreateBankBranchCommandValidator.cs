using FluentValidation;

namespace SmeAccounting.Application.BankBranches.Commands;

public class CreateBankBranchCommandValidator : AbstractValidator<CreateBankBranchCommand>
{
    public CreateBankBranchCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.BankId)
            .GreaterThan(0).WithMessage("Bank ID is required.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Branch code is required.")
            .MaximumLength(50).WithMessage("Branch code cannot exceed 50 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Branch name is required.")
            .MaximumLength(200).WithMessage("Branch name cannot exceed 200 characters.");

        RuleFor(x => x.Description)
            .MaximumLength(500).WithMessage("Description cannot exceed 500 characters.");
    }
}
