using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreatePaymentMethodCommandValidator : AbstractValidator<CreatePaymentMethodCommand>
{
    public CreatePaymentMethodCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Payment method code is required.")
            .MaximumLength(20).WithMessage("Payment method code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Payment method name is required.")
            .MaximumLength(200).WithMessage("Payment method name cannot exceed 200 characters.");

        RuleFor(x => x.Category)
            .IsInEnum().WithMessage("Payment method category is invalid.");

        RuleFor(x => x.Description)
            .MaximumLength(500).WithMessage("Description cannot exceed 500 characters.");
    }
}
