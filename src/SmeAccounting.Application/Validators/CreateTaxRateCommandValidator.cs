using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxRateCommandValidator : AbstractValidator<CreateTaxRateCommand>
{
    public CreateTaxRateCommandValidator()
    {
        RuleFor(x => x.TaxTypeId)
            .GreaterThan(0).WithMessage("Tax type ID is required.");

        RuleFor(x => x.RateValue)
            .GreaterThanOrEqualTo(0).WithMessage("Rate value must be greater than or equal to zero.");

        RuleFor(x => x.RateName)
            .NotEmpty().WithMessage("Rate name is required.")
            .MaximumLength(200).WithMessage("Rate name cannot exceed 200 characters.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
