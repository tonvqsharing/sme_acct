using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.BankTests;

public sealed class ItemBarcodeAggregateTests
{
    [Fact]
    public void ItemBarcode_Ctor_Valid_RaisesItemBarcodeCreatedWithCompanyId()
    {
        var barcode = new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13);

        Assert.Equal(1, barcode.CompanyId);
        Assert.Equal(2, barcode.ItemId);
        Assert.Equal("6291041500213", barcode.Barcode);
        Assert.Equal(BarcodeType.GTIN13, barcode.BarcodeType);
        Assert.True(barcode.IsActive);
        Assert.False(barcode.IsPrimary);
        var evt = Assert.Single(barcode.DomainEvents.OfType<ItemBarcodeCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void CreateItemBarcodeValidator_ValidGtin13_Passes()
    {
        var validator = new CreateItemBarcodeCommandValidator();
        var result = validator.Validate(new CreateItemBarcodeCommand(1, 2, "6291041500213", BarcodeType.GTIN13));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateItemBarcodeValidator_ValidGtin13SecondVector_Passes()
    {
        var validator = new CreateItemBarcodeCommandValidator();
        var result = validator.Validate(new CreateItemBarcodeCommand(1, 2, "5012345670003", BarcodeType.GTIN13));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateItemBarcodeValidator_OtherType_SkipsCheckDigit()
    {
        var validator = new CreateItemBarcodeCommandValidator();
        var result = validator.Validate(new CreateItemBarcodeCommand(1, 2, "INTERNAL-CODE-1", BarcodeType.Other));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task CreateItemBarcodeHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakeItemBarcodeRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateItemBarcodeHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreateItemBarcodeCommand(1, 2, "6291041500213", BarcodeType.GTIN13), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public void ItemBarcode_Ctor_CompanyIdZeroOrNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemBarcode(0, 2, "6291041500213", BarcodeType.GTIN13));
        Assert.Throws<DomainException>(() => new ItemBarcode(-1, 2, "6291041500213", BarcodeType.GTIN13));
    }

    [Fact]
    public void ItemBarcode_Ctor_ItemIdZeroOrNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemBarcode(1, 0, "6291041500213", BarcodeType.GTIN13));
        Assert.Throws<DomainException>(() => new ItemBarcode(1, -1, "6291041500213", BarcodeType.GTIN13));
    }

    [Fact]
    public void ItemBarcode_Ctor_BarcodeWhitespace_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemBarcode(1, 2, " ", BarcodeType.GTIN13));
    }

    [Fact]
    public void ItemBarcode_Ctor_BarcodeLength21_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemBarcode(1, 2, new string('0', 21), BarcodeType.GTIN13));
    }

    [Fact]
    public void ItemBarcode_Ctor_UomIdZeroOrNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13, uomId: 0));
        Assert.Throws<DomainException>(() => new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13, uomId: -1));
    }

    [Fact]
    public void CreateItemBarcodeValidator_InvalidCheckDigit_Fails()
    {
        var validator = new CreateItemBarcodeCommandValidator();
        var result = validator.Validate(new CreateItemBarcodeCommand(1, 2, "6291041500214", BarcodeType.GTIN13));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemBarcodeValidator_WrongLengthGtin_Fails()
    {
        var validator = new CreateItemBarcodeCommandValidator();
        var result = validator.Validate(new CreateItemBarcodeCommand(1, 2, "629104150021", BarcodeType.GTIN13));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemBarcodeValidator_BadBarcodeType_FailsIsInEnum()
    {
        var validator = new CreateItemBarcodeCommandValidator();
        var result = validator.Validate(new CreateItemBarcodeCommand(1, 2, "6291041500213", (BarcodeType)999));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task DeactivateItemBarcodeHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repository = new FakeItemBarcodeRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemBarcodeHandler(repository, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateItemBarcodeCommand(999), CancellationToken.None));
    }

    [Fact]
    public void ItemBarcode_Deactivate_SetsIsActiveFalse()
    {
        var barcode = new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13);

        barcode.Deactivate();

        Assert.False(barcode.IsActive);
    }

    [Fact]
    public async Task DeactivateItemBarcodeHandler_HappyPath_DeactivatesAndSaves()
    {
        var repository = new FakeItemBarcodeRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemBarcodeHandler(repository, unitOfWork);
        var barcode = new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13);
        barcode.Id = 5;
        await repository.AddAsync(barcode);

        await handler.Handle(new DeactivateItemBarcodeCommand(5), CancellationToken.None);

        Assert.False(repository.Stored[0].IsActive);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task ItemBarcodeRepository_GetAllByCompanyAsync_FiltersByCompany()
    {
        var repository = new FakeItemBarcodeRepository();
        await repository.AddAsync(new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13));
        await repository.AddAsync(new ItemBarcode(2, 3, "5012345670003", BarcodeType.GTIN13));

        var companyOne = await repository.GetAllByCompanyAsync(1);

        var only = Assert.Single(companyOne);
        Assert.Equal(1, only.CompanyId);
    }

    [Fact]
    public void ItemBarcode_Deactivate_LeavesIsPrimaryTrue()
    {
        var barcode = new ItemBarcode(1, 2, "6291041500213", BarcodeType.GTIN13, isPrimary: true);

        barcode.Deactivate();

        Assert.False(barcode.IsActive);
        Assert.True(barcode.IsPrimary);
    }
}