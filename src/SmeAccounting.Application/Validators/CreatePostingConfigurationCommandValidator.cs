using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreatePostingConfigurationCommandValidator : AbstractValidator<CreatePostingConfigurationCommand>
{
    public CreatePostingConfigurationCommandValidator()
    {
        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.DebitAccountId)
            .GreaterThan(0).WithMessage("Debit account ID is required.");

        RuleFor(x => x.CreditAccountId)
            .GreaterThan(0).WithMessage("Credit account ID is required.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x)
            .Must(x => x.DebitAccountId != x.CreditAccountId)
            .WithMessage("Debit and credit accounts must be different.");

        RuleFor(x => x.TransactionReasonId)
            .GreaterThan(0).When(x => x.TransactionReasonId.HasValue)
            .WithMessage("Transaction reason ID must be greater than zero when specified.");
    }
}
