using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class ItemPriceListAggregateTests
{
    private static readonly DateOnly EffectiveFrom = new(2026, 1, 1);

    [Fact]
    public void ItemPriceList_Ctor_Valid_RaisesItemPriceListCreatedWithCompanyId()
    {
        var itemPriceList = new ItemPriceList(1, 2, 3, 100m, "USD", EffectiveFrom);

        Assert.Equal(1, itemPriceList.CompanyId);
        Assert.Equal(2, itemPriceList.PriceListId);
        Assert.Equal(3, itemPriceList.ItemId);
        Assert.Equal(100m, itemPriceList.UnitPrice);
        Assert.Equal("USD", itemPriceList.CurrencyCode);
        Assert.Equal(EffectiveFrom, itemPriceList.EffectiveFrom);
        Assert.Null(itemPriceList.EffectiveTo);
        Assert.True(itemPriceList.IsActive);
        var evt = Assert.Single(itemPriceList.DomainEvents.OfType<ItemPriceListCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void ItemPriceList_Ctor_LowercaseCurrencyCode_NormalizedToUppercase()
    {
        var itemPriceList = new ItemPriceList(1, 2, 3, 100m, "usd", EffectiveFrom);

        Assert.Equal("USD", itemPriceList.CurrencyCode);
    }

    [Fact]
    public void ItemPriceList_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(0, 2, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_CompanyIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(-1, 2, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_PriceListIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 0, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_PriceListIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, -1, 3, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_ItemIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 2, 0, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_ItemIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 2, -1, 100m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_UnitPriceNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 2, 3, -1m, "USD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_CurrencyCodeEmpty_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 2, 3, 100m, string.Empty, EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_CurrencyCodeTwoChars_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 2, 3, 100m, "US", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_CurrencyCodeFourChars_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 2, 3, 100m, "USDD", EffectiveFrom));
    }

    [Fact]
    public void ItemPriceList_Ctor_EffectiveToBeforeEffectiveFrom_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemPriceList(1, 2, 3, 100m, "USD", EffectiveFrom, new DateOnly(2025, 12, 31)));
    }

    [Fact]
    public void ItemPriceList_Deactivate_SetsIsActiveFalse()
    {
        var itemPriceList = new ItemPriceList(1, 2, 3, 100m, "USD", EffectiveFrom);

        itemPriceList.Deactivate();

        Assert.False(itemPriceList.IsActive);
    }

    [Fact]
    public void CreateItemPriceListValidator_Valid_Passes()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(1, 2, 3, 100m, "USD", EffectiveFrom));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateItemPriceListValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(0, 2, 3, 100m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemPriceListValidator_PriceListIdZero_Fails()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(1, 0, 3, 100m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemPriceListValidator_ItemIdZero_Fails()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(1, 2, 0, 100m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemPriceListValidator_UnitPriceNegative_Fails()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(1, 2, 3, -1m, "USD", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemPriceListValidator_CurrencyCodeLowercase_Fails()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(1, 2, 3, 100m, "usd", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemPriceListValidator_CurrencyCodeTwoChars_Fails()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(1, 2, 3, 100m, "US", EffectiveFrom));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemPriceListValidator_EffectiveToBeforeEffectiveFrom_Fails()
    {
        var validator = new CreateItemPriceListCommandValidator();
        var result = validator.Validate(new CreateItemPriceListCommand(1, 2, 3, 100m, "USD", EffectiveFrom, new DateOnly(2025, 12, 31)));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateItemPriceListHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakeItemPriceListRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateItemPriceListHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreateItemPriceListCommand(1, 2, 3, 100m, "USD", EffectiveFrom), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal(100m, repository.Stored[0].UnitPrice);
        Assert.Equal("USD", repository.Stored[0].CurrencyCode);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivateItemPriceListHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repository = new FakeItemPriceListRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemPriceListHandler(repository, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateItemPriceListCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivateItemPriceListHandler_HappyPath_DeactivatesAndSaves()
    {
        var repository = new FakeItemPriceListRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemPriceListHandler(repository, unitOfWork);
        var itemPriceList = new ItemPriceList(1, 2, 3, 100m, "USD", EffectiveFrom);
        itemPriceList.Id = 5;
        await repository.AddAsync(itemPriceList);

        await handler.Handle(new DeactivateItemPriceListCommand(5), CancellationToken.None);

        Assert.False(repository.Stored[0].IsActive);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task ItemPriceListRepository_GetAllByCompanyAsync_FiltersByCompany()
    {
        var repository = new FakeItemPriceListRepository();
        await repository.AddAsync(new ItemPriceList(1, 2, 3, 100m, "USD", EffectiveFrom));
        await repository.AddAsync(new ItemPriceList(2, 2, 3, 200m, "USD", EffectiveFrom));

        var result = await repository.GetAllByCompanyAsync(1);

        Assert.Single(result);
        Assert.Equal(1, result[0].CompanyId);
    }
}