using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateOpeningBalanceMappingCommandValidator : AbstractValidator<CreateOpeningBalanceMappingCommand>
{
    public CreateOpeningBalanceMappingCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.DebitAccountId)
            .GreaterThan(0).WithMessage("Debit account ID is required.");

        RuleFor(x => x.CreditAccountId)
            .GreaterThan(0).WithMessage("Credit account ID is required.");

        RuleFor(x => x)
            .Must(x => x.DebitAccountId != x.CreditAccountId)
            .WithMessage("Debit and credit accounts must be different.");
    }
}
