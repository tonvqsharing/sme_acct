using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTransactionReasonCommandValidator : AbstractValidator<CreateTransactionReasonCommand>
{
    public CreateTransactionReasonCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Transaction reason code is required.")
            .MaximumLength(20).WithMessage("Transaction reason code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Transaction reason name is required.")
            .MaximumLength(200).WithMessage("Transaction reason name cannot exceed 200 characters.");

        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
