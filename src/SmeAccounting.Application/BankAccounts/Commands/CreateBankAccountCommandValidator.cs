using FluentValidation;

namespace SmeAccounting.Application.BankAccounts.Commands;

public class CreateBankAccountCommandValidator : AbstractValidator<CreateBankAccountCommand>
{
    public CreateBankAccountCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.BankId)
            .GreaterThan(0).WithMessage("Bank ID is required.");

        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Account code is required.")
            .MaximumLength(50).WithMessage("Account code cannot exceed 50 characters.");

        RuleFor(x => x.AccountNumber)
            .NotEmpty().WithMessage("Account number is required.")
            .MaximumLength(50).WithMessage("Account number cannot exceed 50 characters.");

        RuleFor(x => x.AccountName)
            .NotEmpty().WithMessage("Account name is required.")
            .MaximumLength(200).WithMessage("Account name cannot exceed 200 characters.");

        RuleFor(x => x.Description)
            .MaximumLength(500).WithMessage("Description cannot exceed 500 characters.");

        RuleFor(x => x.CurrencyCode)
            .MaximumLength(3).WithMessage("Currency code cannot exceed 3 characters.")
            .Matches(@"^[A-Z]{3}$").When(x => !string.IsNullOrWhiteSpace(x.CurrencyCode))
            .WithMessage("Currency code must be 3 uppercase letters.");
    }
}
