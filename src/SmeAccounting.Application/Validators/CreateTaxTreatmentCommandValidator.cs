using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxTreatmentCommandValidator : AbstractValidator<CreateTaxTreatmentCommand>
{
    public CreateTaxTreatmentCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Tax treatment code is required.")
            .MaximumLength(20).WithMessage("Tax treatment code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tax treatment name is required.")
            .MaximumLength(200).WithMessage("Tax treatment name cannot exceed 200 characters.");

        RuleFor(x => x.TaxTypeId)
            .GreaterThan(0).WithMessage("Tax type ID is required.");

        RuleFor(x => x.TaxTreatmentType)
            .IsInEnum().WithMessage("Invalid tax treatment type.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
