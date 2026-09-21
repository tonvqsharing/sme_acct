using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class AddOpeningBalanceEntryCommandValidator : AbstractValidator<AddOpeningBalanceEntryCommand>
{
    public AddOpeningBalanceEntryCommandValidator()
    {
        RuleFor(x => x.PeriodId)
            .GreaterThan(0).WithMessage("Period ID is required.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.AccountId)
            .GreaterThan(0).WithMessage("Account ID is required.");

        RuleFor(x => x.Debit)
            .NotNull().WithMessage("Debit is required.");

        RuleFor(x => x.Credit)
            .NotNull().WithMessage("Credit is required.");
    }
}
