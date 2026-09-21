using FluentValidation; using SmeAccounting.Application.Commands;
namespace SmeAccounting.Application.Validators;
public class CreateInventoryAccountingConfigurationCommandValidator : AbstractValidator<CreateInventoryAccountingConfigurationCommand>
{
    public CreateInventoryAccountingConfigurationCommandValidator()
    {
        RuleFor(x => x.CompanyId).GreaterThan(0);
        RuleFor(x => x.InventoryAccountId).GreaterThan(0);
        RuleFor(x => x.CogsAccountId).GreaterThan(0);
        RuleFor(x => x).Must(x => x.InventoryAccountId != x.CogsAccountId).WithMessage("Inventory and COGS accounts must differ");
    }
}
