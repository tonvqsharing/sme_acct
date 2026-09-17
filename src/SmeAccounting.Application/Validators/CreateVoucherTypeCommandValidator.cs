using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateVoucherTypeCommandValidator : AbstractValidator<CreateVoucherTypeCommand>
{
    public CreateVoucherTypeCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Voucher type code is required.")
            .MaximumLength(20).WithMessage("Voucher type code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Voucher type name is required.")
            .MaximumLength(200).WithMessage("Voucher type name cannot exceed 200 characters.");

        RuleFor(x => x.VoucherCategory)
            .IsInEnum().WithMessage("Invalid voucher category.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
