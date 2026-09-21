using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateOpeningBalancePeriodCommandValidator : AbstractValidator<CreateOpeningBalancePeriodCommand>
{
    public CreateOpeningBalancePeriodCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.FiscalPeriodId)
            .GreaterThan(0).WithMessage("Fiscal period ID is required.");

        RuleFor(x => x.PeriodDate)
            .NotEmpty().WithMessage("Period date is required.");
    }
}
