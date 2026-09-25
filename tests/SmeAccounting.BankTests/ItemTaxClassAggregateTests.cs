using SmeAccounting.Application.Commands;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Queries;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class ItemTaxClassAggregateTests
{
    private static readonly DateOnly EffectiveFrom = new(2026, 1, 1);

    [Fact]
    public void ItemTaxClass_Ctor_Valid_RaisesItemTaxClassCreatedWithCompanyId()
    {
        var entity = new ItemTaxClass(1, 2, 3, EffectiveFrom, null);

        Assert.Equal(1, entity.CompanyId);
        Assert.Equal(2, entity.ItemId);
        Assert.Equal(3, entity.TaxTypeId);
        Assert.Equal(EffectiveFrom, entity.EffectiveFrom);
        Assert.Null(entity.EffectiveTo);
        Assert.True(entity.IsActive);
        var evt = Assert.Single(entity.DomainEvents.OfType<ItemTaxClassCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void ItemTaxClass_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemTaxClass(0, 2, 3, EffectiveFrom));
    }

    [Fact]
    public void ItemTaxClass_Ctor_CompanyIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemTaxClass(-1, 2, 3, EffectiveFrom));
    }

    [Fact]
    public void ItemTaxClass_Ctor_ItemIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemTaxClass(1, 0, 3, EffectiveFrom));
    }

    [Fact]
    public void ItemTaxClass_Ctor_ItemIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemTaxClass(1, -1, 3, EffectiveFrom));
    }

    [Fact]
    public void ItemTaxClass_Ctor_TaxTypeIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemTaxClass(1, 2, 0, EffectiveFrom));
    }

    [Fact]
    public void ItemTaxClass_Ctor_TaxTypeIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemTaxClass(1, 2, -1, EffectiveFrom));
    }

    [Fact]
    public void ItemTaxClass_Ctor_EffectiveToBeforeEffectiveFrom_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemTaxClass(1, 2, 3, EffectiveFrom.AddDays(5), EffectiveFrom));
    }

    [Fact]
    public void ItemTaxClass_Deactivate_SetsIsActiveFalse()
    {
        var entity = new ItemTaxClass(1, 2, 3, EffectiveFrom);
        entity.Deactivate();
        Assert.False(entity.IsActive);
    }

    [Fact]
    public void CreateItemTaxClassValidator_Valid_Passes()
    {
        var validator = new CreateItemTaxClassCommandValidator();
        var result = validator.Validate(new CreateItemTaxClassCommand(1, 2, 3, EffectiveFrom, EffectiveFrom.AddDays(10)));
        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateItemTaxClassValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateItemTaxClassCommandValidator();
        var result = validator.Validate(new CreateItemTaxClassCommand(0, 2, 3, EffectiveFrom));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemTaxClassValidator_ItemIdZero_Fails()
    {
        var validator = new CreateItemTaxClassCommandValidator();
        var result = validator.Validate(new CreateItemTaxClassCommand(1, 0, 3, EffectiveFrom));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemTaxClassValidator_TaxTypeIdZero_Fails()
    {
        var validator = new CreateItemTaxClassCommandValidator();
        var result = validator.Validate(new CreateItemTaxClassCommand(1, 2, 0, EffectiveFrom));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemTaxClassValidator_EffectiveToBeforeEffectiveFrom_Fails()
    {
        var validator = new CreateItemTaxClassCommandValidator();
        var result = validator.Validate(new CreateItemTaxClassCommand(1, 2, 3, EffectiveFrom.AddDays(5), EffectiveFrom));
        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateItemTaxClassHandler_HappyPath_AddsAndSaves()
    {
        var repo = new FakeItemTaxClassRepository();
        var uow = new FakeUnitOfWork();
        var handler = new CreateItemTaxClassHandler(repo, uow);

        var result = await handler.Handle(new CreateItemTaxClassCommand(1, 2, 3, EffectiveFrom, EffectiveFrom.AddDays(10)), CancellationToken.None);

        Assert.Single(repo.Stored);
        Assert.Equal(repo.Stored[0].Id, result.Id);
        Assert.Equal(1, uow.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivateItemTaxClassHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repo = new FakeItemTaxClassRepository();
        var uow = new FakeUnitOfWork();
        var handler = new DeactivateItemTaxClassHandler(repo, uow);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateItemTaxClassCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivateItemTaxClassHandler_HappyPath_DeactivatesAndSaves()
    {
        var repo = new FakeItemTaxClassRepository();
        var uow = new FakeUnitOfWork();
        var handler = new DeactivateItemTaxClassHandler(repo, uow);

        var entity = new ItemTaxClass(1, 2, 3, EffectiveFrom);
        entity.Id = 5;
        await repo.AddAsync(entity);

        await handler.Handle(new DeactivateItemTaxClassCommand(5), CancellationToken.None);

        Assert.False(repo.Stored[0].IsActive);
        Assert.Equal(1, uow.SaveCalledCount);
    }

    [Fact]
    public async Task GetItemTaxClassHandler_GetById_ReturnsDto()
    {
        var repo = new FakeItemTaxClassRepository();
        var handler = new GetItemTaxClassHandler(repo);
        var entity = new ItemTaxClass(1, 2, 3, EffectiveFrom, EffectiveFrom.AddDays(10));
        entity.Id = 7;
        await repo.AddAsync(entity);

        var dto = await handler.Handle(new GetItemTaxClassQuery(7), CancellationToken.None);

        Assert.NotNull(dto);
        Assert.Equal(7, dto!.Id);
        Assert.Equal(1, dto.CompanyId);
        Assert.Equal(2, dto.ItemId);
        Assert.Equal(3, dto.TaxTypeId);
    }

    [Fact]
    public async Task GetItemTaxClassHandler_GetByCompany_ReturnsList()
    {
        var repo = new FakeItemTaxClassRepository();
        var handler = new GetItemTaxClassHandler(repo);

        var entity1 = new ItemTaxClass(1, 2, 3, EffectiveFrom);
        entity1.Id = 8;
        await repo.AddAsync(entity1);

        var entity2 = new ItemTaxClass(2, 3, 4, EffectiveFrom);
        entity2.Id = 9;
        await repo.AddAsync(entity2);

        var dtos = await handler.Handle(new GetItemTaxClassesByCompanyQuery(1), CancellationToken.None);

        Assert.Single(dtos);
        Assert.Equal(1, dtos[0].CompanyId);
    }
}