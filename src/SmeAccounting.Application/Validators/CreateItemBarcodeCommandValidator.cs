using FluentValidation;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Validators;

public class CreateItemBarcodeCommandValidator : AbstractValidator<CreateItemBarcodeCommand>
{
    public CreateItemBarcodeCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.ItemId)
            .GreaterThan(0).WithMessage("Item ID is required.");

        RuleFor(x => x.Barcode)
            .NotEmpty().WithMessage("Barcode is required.")
            .MaximumLength(20).WithMessage("Barcode cannot exceed 20 characters.");

        RuleFor(x => x.UomId)
            .GreaterThan(0).WithMessage("UOM ID must be greater than zero when specified.")
            .When(x => x.UomId.HasValue);

        RuleFor(x => x.BarcodeType)
            .IsInEnum().WithMessage("Barcode type is invalid.");

        RuleFor(x => x)
            .Must(x => HasValidCheckDigit(x.Barcode, x.BarcodeType))
            .WithMessage("Barcode fails the GS1 Mod-10 check digit validation.")
            .When(x => x.BarcodeType != BarcodeType.Other);
    }

    private static bool HasValidCheckDigit(string barcode, BarcodeType type)
    {
        if (string.IsNullOrWhiteSpace(barcode) || !barcode.All(char.IsDigit))
            return false;

        int dataLength = type switch
        {
            BarcodeType.GTIN8 => 7,
            BarcodeType.GTIN12 => 11,
            BarcodeType.GTIN13 => 12,
            BarcodeType.GTIN14 => 13,
            _ => 0
        };

        if (barcode.Length != dataLength + 1)
            return false;

        int sum = 0;
        for (int i = dataLength - 1; i >= 0; i--)
        {
            int digit = barcode[i] - '0';
            int weight = (dataLength - 1 - i) % 2 == 0 ? 3 : 1;
            sum += digit * weight;
        }

        int checkDigit = (10 - (sum % 10)) % 10;
        return checkDigit == barcode[dataLength] - '0';
    }
}