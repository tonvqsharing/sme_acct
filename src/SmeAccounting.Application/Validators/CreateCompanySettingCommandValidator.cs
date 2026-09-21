using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateCompanySettingCommandValidator : AbstractValidator<CreateCompanySettingCommand>
{
    public CreateCompanySettingCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID must be greater than zero.");

        RuleFor(x => x.LegalRepresentativeName)
            .NotEmpty().WithMessage("Legal representative name is required.")
            .MaximumLength(200).WithMessage("Legal representative name cannot exceed 200 characters.");

        RuleFor(x => x.LegalRepresentativeTaxId)
            .NotEmpty().WithMessage("Legal representative tax ID is required.")
            .MaximumLength(50).WithMessage("Legal representative tax ID cannot exceed 50 characters.");

        RuleFor(x => x.ChiefAccountantName)
            .MaximumLength(200).WithMessage("Chief accountant name cannot exceed 200 characters.");

        RuleFor(x => x.ChiefAccountantTaxId)
            .MaximumLength(50).WithMessage("Chief accountant tax ID cannot exceed 50 characters.");

        RuleFor(x => x.FiscalYearStartMonth)
            .InclusiveBetween(1, 12).When(x => x.FiscalYearStartMonth.HasValue)
            .WithMessage("Fiscal year start month must be between 1 and 12.");

        RuleFor(x => x.Currency)
            .MaximumLength(3).When(x => !string.IsNullOrWhiteSpace(x.Currency))
            .WithMessage("Currency code cannot exceed 3 characters.");
    }
}
