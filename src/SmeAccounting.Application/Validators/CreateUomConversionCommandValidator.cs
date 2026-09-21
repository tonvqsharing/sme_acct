using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateUomConversionCommandValidator : AbstractValidator<CreateUomConversionCommand>
{
    public CreateUomConversionCommandValidator()
    {
        RuleFor(x => x.CompanyId).GreaterThan(0);
        RuleFor(x => x.FromUomId).GreaterThan(0);
        RuleFor(x => x.ToUomId).GreaterThan(0);
        RuleFor(x => x.Factor).GreaterThan(0);
        RuleFor(x => x).Must(x => x.FromUomId != x.ToUomId).WithMessage("From and To UOM must be different");
    }
}
