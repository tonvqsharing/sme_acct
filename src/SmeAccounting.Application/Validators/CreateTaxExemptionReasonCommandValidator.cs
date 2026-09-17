using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxExemptionReasonCommandValidator : AbstractValidator<CreateTaxExemptionReasonCommand>
{
    public CreateTaxExemptionReasonCommandValidator()
    {
        RuleFor(x => x.TaxTypeId)
            .GreaterThan(0).WithMessage("Tax type ID is required.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Tax exemption reason code is required.")
            .MaximumLength(20).WithMessage("Tax exemption reason code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Tax exemption reason name is required.")
            .MaximumLength(200).WithMessage("Tax exemption reason name cannot exceed 200 characters.");

        RuleFor(x => x.LegalBasis)
            .NotEmpty().WithMessage("Legal basis is required.")
            .MaximumLength(500).WithMessage("Legal basis cannot exceed 500 characters.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
