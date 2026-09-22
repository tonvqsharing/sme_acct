using FluentValidation;
using SmeAccounting.Application.Banks.Commands;

namespace SmeAccounting.Application.Banks.Commands;

public class CreateBankCommandValidator : AbstractValidator<CreateBankCommand>
{
    public CreateBankCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Bank code is required.")
            .MaximumLength(50).WithMessage("Bank code cannot exceed 50 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Bank name is required.")
            .MaximumLength(200).WithMessage("Bank name cannot exceed 200 characters.");

        RuleFor(x => x.Description)
            .MaximumLength(500).WithMessage("Description cannot exceed 500 characters.");
    }
}
