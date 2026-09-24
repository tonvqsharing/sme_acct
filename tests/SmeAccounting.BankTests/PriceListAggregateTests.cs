using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class PriceListAggregateTests
{
    [Fact]
    public void PriceList_Ctor_Valid_RaisesPriceListCreatedWithCompanyId()
    {
        var priceList = new PriceList(1, "PL1", "Retail Price List");

        Assert.Equal(1, priceList.CompanyId);
        Assert.Equal("PL1", priceList.Code);
        Assert.Equal("Retail Price List", priceList.Name);
        Assert.True(priceList.IsActive);
        var evt = Assert.Single(priceList.DomainEvents.OfType<PriceListCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void PriceList_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PriceList(0, "PL1", "Retail Price List"));
    }

    [Fact]
    public void PriceList_Ctor_CompanyIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PriceList(-1, "PL1", "Retail Price List"));
    }

    [Fact]
    public void PriceList_Ctor_EmptyCode_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PriceList(1, string.Empty, "Retail Price List"));
    }

    [Fact]
    public void PriceList_Ctor_EmptyName_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PriceList(1, "PL1", "  "));
    }

    [Fact]
    public void PriceList_Deactivate_SetsIsActiveFalse()
    {
        var priceList = new PriceList(1, "PL1", "Retail Price List");

        priceList.Deactivate();

        Assert.False(priceList.IsActive);
    }

    [Fact]
    public void CreatePriceListValidator_Valid_Passes()
    {
        var validator = new CreatePriceListCommandValidator();
        var result = validator.Validate(new CreatePriceListCommand(1, "PL1", "Retail Price List"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreatePriceListValidator_CompanyIdZero_Fails()
    {
        var validator = new CreatePriceListCommandValidator();
        var result = validator.Validate(new CreatePriceListCommand(0, "PL1", "Retail Price List"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreatePriceListValidator_EmptyCode_Fails()
    {
        var validator = new CreatePriceListCommandValidator();
        var result = validator.Validate(new CreatePriceListCommand(1, string.Empty, "Retail Price List"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreatePriceListValidator_EmptyName_Fails()
    {
        var validator = new CreatePriceListCommandValidator();
        var result = validator.Validate(new CreatePriceListCommand(1, "PL1", string.Empty));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreatePriceListValidator_OverLength_Fails()
    {
        var validator = new CreatePriceListCommandValidator();

        Assert.False(validator.Validate(new CreatePriceListCommand(1, new string('X', 21), "Retail Price List")).IsValid);
        Assert.False(validator.Validate(new CreatePriceListCommand(1, "PL1", new string('X', 201))).IsValid);
        Assert.False(validator.Validate(new CreatePriceListCommand(1, "PL1", "Retail Price List", Description: new string('X', 501))).IsValid);
    }

    [Fact]
    public async Task CreatePriceListHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakePriceListRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreatePriceListHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreatePriceListCommand(1, "PL1", "Retail Price List"), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal("PL1", repository.Stored[0].Code);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivatePriceListHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repository = new FakePriceListRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivatePriceListHandler(repository, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivatePriceListCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivatePriceListHandler_HappyPath_DeactivatesAndSaves()
    {
        var repository = new FakePriceListRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivatePriceListHandler(repository, unitOfWork);
        var priceList = new PriceList(1, "PL1", "Retail Price List");
        priceList.Id = 5;
        await repository.AddAsync(priceList);

        await handler.Handle(new DeactivatePriceListCommand(5), CancellationToken.None);

        Assert.False(repository.Stored[0].IsActive);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task PriceListRepository_GetAllByCompanyAsync_FiltersByCompany()
    {
        var repository = new FakePriceListRepository();
        await repository.AddAsync(new PriceList(1, "PL1", "Company One List"));
        await repository.AddAsync(new PriceList(2, "PL2", "Company Two List"));

        var result = await repository.GetAllByCompanyAsync(1);

        Assert.Single(result);
        Assert.Equal(1, result[0].CompanyId);
    }
}