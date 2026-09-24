using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateItemPriceListCommandValidator : AbstractValidator<CreateItemPriceListCommand>
{
    public CreateItemPriceListCommandValidator()
    {
        RuleFor(x => x.CompanyId).GreaterThan(0);
        RuleFor(x => x.PriceListId).GreaterThan(0);
        RuleFor(x => x.ItemId).GreaterThan(0);
        RuleFor(x => x.UnitPrice).GreaterThanOrEqualTo(0);
        RuleFor(x => x.CurrencyCode).NotEmpty().Length(3).Matches("^[A-Z]{3}$");
        RuleFor(x => x.EffectiveFrom).NotEmpty();
        RuleFor(x => x).Must(x => !x.EffectiveTo.HasValue || x.EffectiveTo >= x.EffectiveFrom)
            .WithMessage("EffectiveTo must be null or on/after EffectiveFrom.");
    }
}