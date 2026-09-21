using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class PostOpeningBalancesCommandValidator : AbstractValidator<PostOpeningBalancesCommand>
{
    public PostOpeningBalancesCommandValidator()
    {
        RuleFor(x => x.PeriodId)
            .GreaterThan(0).WithMessage("Period ID is required.");

        RuleFor(x => x.PostedBy)
            .NotEmpty().WithMessage("Posted by is required.");

        RuleFor(x => x.PostedAt)
            .NotEmpty().WithMessage("Posted at is required.");
    }
}
