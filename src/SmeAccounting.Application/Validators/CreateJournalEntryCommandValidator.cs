using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateJournalEntryCommandValidator : AbstractValidator<CreateJournalEntryCommand>
{
    public CreateJournalEntryCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.PeriodId)
            .GreaterThan(0).WithMessage("Period ID is required.");

        RuleFor(x => x.Lines)
            .NotEmpty().WithMessage("Journal entry must have at least one line.");

        RuleForEach(x => x.Lines).ChildRules(line =>
        {
            line.RuleFor(l => l.AccountId)
                .GreaterThan(0).WithMessage("Line must have a valid account.");
        });
    }
}
