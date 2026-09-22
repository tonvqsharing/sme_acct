using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreatePostingReferenceCommandValidator : AbstractValidator<CreatePostingReferenceCommand>
{
    public CreatePostingReferenceCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.JournalEntryId)
            .GreaterThan(0).WithMessage("Journal entry ID is required.");

        RuleFor(x => x.SourceType)
            .NotEmpty().WithMessage("Source type is required.")
            .MaximumLength(100).WithMessage("Source type cannot exceed 100 characters.");

        RuleFor(x => x.SourceId)
            .GreaterThan(0).WithMessage("Source ID is required.");
    }
}
