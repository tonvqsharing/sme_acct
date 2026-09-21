using FluentValidation; using SmeAccounting.Application.Commands;
namespace SmeAccounting.Application.Validators;
public class CreateInventoryValuationPolicyCommandValidator : AbstractValidator<CreateInventoryValuationPolicyCommand>
{
    public CreateInventoryValuationPolicyCommandValidator()
    {
        RuleFor(x => x.CompanyId).GreaterThan(0);
        RuleFor(x => x.Code).NotEmpty().MaximumLength(20);
        RuleFor(x => x.Name).NotEmpty().MaximumLength(200);
        RuleFor(x => x.ValuationMethod).NotEmpty();
    }
}
