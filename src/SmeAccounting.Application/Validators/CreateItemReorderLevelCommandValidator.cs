using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateItemReorderLevelCommandValidator : AbstractValidator<CreateItemReorderLevelCommand>
{
    public CreateItemReorderLevelCommandValidator()
    {
        RuleFor(x => x.CompanyId).GreaterThan(0);
        RuleFor(x => x.ItemId).GreaterThan(0);
        RuleFor(x => x.MinimumQuantity).GreaterThanOrEqualTo(0);
        RuleFor(x => x.WarehouseId).GreaterThan(0).When(x => x.WarehouseId.HasValue);
        RuleFor(x => x.MaximumQuantity).GreaterThanOrEqualTo(0).When(x => x.MaximumQuantity.HasValue);
        RuleFor(x => x).Must(x => !x.MaximumQuantity.HasValue || x.MaximumQuantity >= x.MinimumQuantity)
            .WithMessage("MaximumQuantity must be greater than or equal to MinimumQuantity");
    }
}
