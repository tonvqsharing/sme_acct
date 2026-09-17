using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreatePaymentTermCommandValidator : AbstractValidator<CreatePaymentTermCommand>
{
    public CreatePaymentTermCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Payment term code is required.")
            .MaximumLength(20).WithMessage("Payment term code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Payment term name is required.")
            .MaximumLength(200).WithMessage("Payment term name cannot exceed 200 characters.");

        RuleFor(x => x.PaymentTermType)
            .IsInEnum().WithMessage("Payment term type is invalid.");

        RuleFor(x => x.Days)
            .GreaterThanOrEqualTo(0).When(x => x.Days.HasValue).WithMessage("Days must be greater than or equal to zero.");

        RuleFor(x => x.Description)
            .MaximumLength(500).WithMessage("Description cannot exceed 500 characters.");
    }
}
