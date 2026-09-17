using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTaxAccountingMappingCommandValidator : AbstractValidator<CreateTaxAccountingMappingCommand>
{
    public CreateTaxAccountingMappingCommandValidator()
    {
        RuleFor(x => x.TaxTypeId)
            .GreaterThan(0).WithMessage("Tax type ID is required.");

        RuleFor(x => x.TaxTreatmentId)
            .GreaterThan(0).WithMessage("Tax treatment ID is required.");

        RuleFor(x => x.AccountId)
            .GreaterThan(0).WithMessage("Account ID is required.");

        RuleFor(x => x.MappingType)
            .IsInEnum().WithMessage("Invalid mapping type.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
