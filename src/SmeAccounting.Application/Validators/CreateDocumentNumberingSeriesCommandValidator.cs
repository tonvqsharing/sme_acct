using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateDocumentNumberingSeriesCommandValidator : AbstractValidator<CreateDocumentNumberingSeriesCommand>
{
    public CreateDocumentNumberingSeriesCommandValidator()
    {
        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.Prefix)
            .NotEmpty().WithMessage("Prefix is required.")
            .MaximumLength(20).WithMessage("Prefix cannot exceed 20 characters.");

        RuleFor(x => x.PaddingLength)
            .InclusiveBetween(1, 10).WithMessage("Padding length must be between 1 and 10.");
    }
}
