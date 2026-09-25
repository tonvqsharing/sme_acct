using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class ItemSupplierPriceAggregateTests
{
    private static readonly DateOnly EffectiveFrom = new(2026, 1, 1);

    [Fact]
    public void ItemSupplierPrice_Ctor_Valid_RaisesItemSupplierPriceCreatedWithCompanyId()
    {
        var itemSupplierPrice = new ItemSupplierPrice(1, 2, 3, 100m, "USD", EffectiveFrom);

        Assert.Equal(1, itemSupplierPrice.CompanyId);
        Assert.Equal(2, itemSupplierPrice.SupplierId);
        Assert.Equal(3, itemSupplierPrice.ItemId);
        Assert.Equal(100m, itemSupplierPrice.UnitPrice);
        Assert.Equal("USD", itemSupplierPrice.CurrencyCode);
        Assert.Equal(EffectiveFrom, itemSupplierPrice.EffectiveFrom);
        Assert.Null(itemSupplierPrice.EffectiveTo);
        Assert.True(itemSupplierPrice.IsActive);
        var evt = Assert.Single(itemSupplierPrice.DomainEvents.OfType<ItemSupplierPriceCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_LowercaseCurrencyCode_NormalizedToUppercase()
    {
        var itemSupplierPrice = new ItemSupplierPrice(1, 2, 3, 100m, "usd", EffectiveFrom);

        Assert.Equal("USD", itemSupplierPrice.CurrencyCode);
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(0, 2, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_CompanyIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(-1, 2, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_SupplierIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 0, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_SupplierIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, -1, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_ItemIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 2, 0, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_ItemIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 2, -1, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_UnitPriceNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 2, 3, -1m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_CurrencyCodeEmpty_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 2, 3, 100m, string.Empty, EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_CurrencyCodeTwoChars_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 2, 3, 100m, "US", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_CurrencyCodeFourChars_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 2, 3, 100m, "USDD", EffectiveFrom));
    }

    [Fact]
    public void ItemSupplierPrice_Ctor_EffectiveToBeforeEffectiveFrom_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemSupplierPrice(1, 2, 3, 100m, "USD", EffectiveFrom, new DateOnly(2025, 12, 31)));
    }

    [Fact]
    public void ItemSupplierPrice_Deactivate_SetsIsActiveFalse()
    {
        var itemSupplierPrice = new ItemSupplierPrice(1, 2, 3, 100m, "USD", EffectiveFrom);

        itemSupplierPrice.Deactivate();

        Assert.False(itemSupplierPrice.IsActive);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_Valid_Passes()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(1, 2, 3, 100m, "USD", EffectiveFrom));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(0, 2, 3, 100m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_SupplierIdZero_Fails()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(1, 0, 3, 100m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_ItemIdZero_Fails()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(1, 2, 0, 100m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_UnitPriceNegative_Fails()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(1, 2, 3, -1m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_CurrencyCodeLowercase_Fails()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(1, 2, 3, 100m, "usd", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_CurrencyCodeTwoChars_Fails()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(1, 2, 3, 100m, "US", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemSupplierPriceValidator_EffectiveToBeforeEffectiveFrom_Fails()
    {
        var validator = new CreateItemSupplierPriceCommandValidator();
        var result = validator.Validate(new CreateItemSupplierPriceCommand(1, 2, 3, 100m, "USD", EffectiveFrom, new DateOnly(2025, 12, 31)));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateItemSupplierPriceHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakeItemSupplierPriceRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateItemSupplierPriceHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreateItemSupplierPriceCommand(1, 2, 3, 100m, "USD", EffectiveFrom), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal(100m, repository.Stored[0].UnitPrice);
        Assert.Equal("USD", repository.Stored[0].CurrencyCode);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivateItemSupplierPriceHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repository = new FakeItemSupplierPriceRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemSupplierPriceHandler(repository, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateItemSupplierPriceCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivateItemSupplierPriceHandler_HappyPath_DeactivatesAndSaves()
    {
        var repository = new FakeItemSupplierPriceRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemSupplierPriceHandler(repository, unitOfWork);
        var itemSupplierPrice = new ItemSupplierPrice(1, 2, 3, 100m, "USD", EffectiveFrom);
        itemSupplierPrice.Id = 5;
        await repository.AddAsync(itemSupplierPrice);

        await handler.Handle(new DeactivateItemSupplierPriceCommand(5), CancellationToken.None);

        Assert.False(repository.Stored[0].IsActive);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task ItemSupplierPriceRepository_GetAllByCompanyAsync_FiltersByCompany()
    {
        var repository = new FakeItemSupplierPriceRepository();
        await repository.AddAsync(new ItemSupplierPrice(1, 2, 3, 100m, "USD", EffectiveFrom));
        await repository.AddAsync(new ItemSupplierPrice(2, 2, 3, 200m, "USD", EffectiveFrom));

        var result = await repository.GetAllByCompanyAsync(1);

        Assert.Single(result);
        Assert.Equal(1, result[0].CompanyId);
    }
}
