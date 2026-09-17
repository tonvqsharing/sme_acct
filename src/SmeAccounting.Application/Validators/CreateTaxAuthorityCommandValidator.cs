using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxAuthorityCommandValidator : AbstractValidator<CreateTaxAuthorityCommand>
{
    public CreateTaxAuthorityCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Tax authority code is required.")
            .MaximumLength(20).WithMessage("Tax authority code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tax authority name is required.")
            .MaximumLength(200).WithMessage("Tax authority name cannot exceed 200 characters.");

        RuleFor(x => x.AuthorityLevel)
            .IsInEnum().WithMessage("Invalid authority level.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
