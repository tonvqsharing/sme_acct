using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxTypeCommandValidator : AbstractValidator<CreateTaxTypeCommand>
{
    public CreateTaxTypeCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Tax type code is required.")
            .MaximumLength(20).WithMessage("Tax type code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tax type name is required.")
            .MaximumLength(200).WithMessage("Tax type name cannot exceed 200 characters.");

        RuleFor(x => x.TaxCategory)
            .IsInEnum().WithMessage("Invalid tax category.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
