using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateItemCommandValidator : AbstractValidator<CreateItemCommand>
{
    public CreateItemCommandValidator()
    {
        RuleFor(x => x.CompanyId).GreaterThan(0);
        RuleFor(x => x.Code).NotEmpty().MaximumLength(20);
        RuleFor(x => x.Name).NotEmpty().MaximumLength(200);
        RuleFor(x => x.IsStockItem).NotNull();
        RuleFor(x => x.IsServiceItem).NotNull();
        RuleFor(x => x).Must(x => x.IsStockItem || x.IsServiceItem).WithMessage("Item must be stock or service");
        RuleFor(x => x.UomId).NotNull().When(x => x.IsStockItem);
    }
}
