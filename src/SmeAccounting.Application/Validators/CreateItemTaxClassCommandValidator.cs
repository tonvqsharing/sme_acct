using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateItemTaxClassCommandValidator : AbstractValidator<CreateItemTaxClassCommand>
{
    public CreateItemTaxClassCommandValidator()
    {
        RuleFor(x => x.CompanyId).GreaterThan(0);
        RuleFor(x => x.ItemId).GreaterThan(0);
        RuleFor(x => x.TaxTypeId).GreaterThan(0);
        RuleFor(x => x.EffectiveFrom).NotEmpty();
        RuleFor(x => x).Must(x => !x.EffectiveTo.HasValue || x.EffectiveTo >= x.EffectiveFrom)
            .WithMessage("EffectiveTo must be null or on/after EffectiveFrom.");
    }
}