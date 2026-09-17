using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxRuleCommandValidator : AbstractValidator<CreateTaxRuleCommand>
{
    public CreateTaxRuleCommandValidator()
    {
        RuleFor(x => x.TaxTypeId)
            .GreaterThan(0).WithMessage("Tax type ID is required.");

        RuleFor(x => x.TaxRateId)
            .GreaterThan(0).When(x => x.TaxRateId.HasValue)
            .WithMessage("Tax rate ID must be greater than zero when provided.");

        RuleFor(x => x.TaxTreatmentId)
            .GreaterThan(0).WithMessage("Tax treatment ID is required.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Tax rule code is required.")
            .MaximumLength(20).WithMessage("Tax rule code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tax rule name is required.")
            .MaximumLength(200).WithMessage("Tax rule name cannot exceed 200 characters.");

        RuleFor(x => x.LegalReference)
            .NotEmpty().WithMessage("Legal reference is required.")
            .MaximumLength(500).WithMessage("Legal reference cannot exceed 500 characters.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
