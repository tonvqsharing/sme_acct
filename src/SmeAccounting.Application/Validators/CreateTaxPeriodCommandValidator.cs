using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxPeriodCommandValidator : AbstractValidator<CreateTaxPeriodCommand>
{
    public CreateTaxPeriodCommandValidator()
    {
        RuleFor(x => x.FiscalPeriodId)
            .GreaterThan(0).WithMessage("Fiscal period ID is required.");

        RuleFor(x => x.TaxTypeId)
            .GreaterThan(0).WithMessage("Tax type ID is required.");

        RuleFor(x => x.FilingFrequency)
            .IsInEnum().WithMessage("Invalid filing frequency.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
