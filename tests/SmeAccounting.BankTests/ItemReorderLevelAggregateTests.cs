using SmeAccounting.Application.Commands;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Queries;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class ItemReorderLevelAggregateTests
{
    [Fact]
    public void ItemReorderLevel_Ctor_Valid_RaisesItemReorderLevelCreatedWithCompanyId()
    {
        var entity = new ItemReorderLevel(1, 2, 10m, 3, 20m);

        Assert.Equal(1, entity.CompanyId);
        Assert.Equal(2, entity.ItemId);
        Assert.Equal(3, entity.WarehouseId);
        Assert.Equal(10m, entity.MinimumQuantity);
        Assert.Equal(20m, entity.MaximumQuantity);
        Assert.True(entity.IsActive);
        var evt = Assert.Single(entity.DomainEvents.OfType<ItemReorderLevelCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void ItemReorderLevel_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemReorderLevel(0, 2, 10m));
    }

    [Fact]
    public void ItemReorderLevel_Ctor_ItemIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemReorderLevel(1, 0, 10m));
    }

    [Fact]
    public void ItemReorderLevel_Ctor_WarehouseIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemReorderLevel(1, 2, 10m, 0));
    }

    [Fact]
    public void ItemReorderLevel_Ctor_MinimumQuantityNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemReorderLevel(1, 2, -1m));
    }

    [Fact]
    public void ItemReorderLevel_Ctor_MaximumQuantityLessThanMinimum_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemReorderLevel(1, 2, 10m, null, 5m));
    }

    [Fact]
    public void ItemReorderLevel_Deactivate_SetsIsActiveFalse()
    {
        var entity = new ItemReorderLevel(1, 2, 10m);

        entity.Deactivate();

        Assert.False(entity.IsActive);
    }

    [Fact]
    public void CreateItemReorderLevelValidator_Valid_Passes()
    {
        var validator = new CreateItemReorderLevelCommandValidator();
        var result = validator.Validate(new CreateItemReorderLevelCommand(1, 2, 10m, 3, 20m));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateItemReorderLevelValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateItemReorderLevelCommandValidator();
        var result = validator.Validate(new CreateItemReorderLevelCommand(0, 2, 10m));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemReorderLevelValidator_ItemIdZero_Fails()
    {
        var validator = new CreateItemReorderLevelCommandValidator();
        var result = validator.Validate(new CreateItemReorderLevelCommand(1, 0, 10m));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemReorderLevelValidator_MinimumQuantityNegative_Fails()
    {
        var validator = new CreateItemReorderLevelCommandValidator();
        var result = validator.Validate(new CreateItemReorderLevelCommand(1, 2, -1m));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemReorderLevelValidator_MaximumLessThanMinimum_Fails()
    {
        var validator = new CreateItemReorderLevelCommandValidator();
        var result = validator.Validate(new CreateItemReorderLevelCommand(1, 2, 10m, null, 5m));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateItemReorderLevelHandler_ItemNotFound_ThrowsInvalidOperationException()
    {
        var repo = new FakeItemReorderLevelRepository();
        var itemRepo = new FakeItemRepository();
        var uow = new FakeUnitOfWork();
        var handler = new CreateItemReorderLevelHandler(repo, itemRepo, uow);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new CreateItemReorderLevelCommand(1, 999, 10m), CancellationToken.None));
    }

    [Fact]
    public async Task CreateItemReorderLevelHandler_ItemNotStock_ThrowsDomainException()
    {
        var repo = new FakeItemReorderLevelRepository();
        var itemRepo = new FakeItemRepository();
        var uow = new FakeUnitOfWork();
        var handler = new CreateItemReorderLevelHandler(repo, itemRepo, uow);

        var item = new Item(1, "CODE", "Name", false, true, null, null, null, null);
        item.Id = 2;
        await itemRepo.AddAsync(item);

        await Assert.ThrowsAsync<DomainException>(() => handler.Handle(new CreateItemReorderLevelCommand(1, 2, 10m), CancellationToken.None));
    }

    [Fact]
    public async Task CreateItemReorderLevelHandler_HappyPath_AddsAndSaves()
    {
        var repo = new FakeItemReorderLevelRepository();
        var itemRepo = new FakeItemRepository();
        var uow = new FakeUnitOfWork();
        var handler = new CreateItemReorderLevelHandler(repo, itemRepo, uow);

        var item = new Item(1, "CODE", "Name", true, false, null, 5, null, null);
        item.Id = 2;
        await itemRepo.AddAsync(item);

        var result = await handler.Handle(new CreateItemReorderLevelCommand(1, 2, 10m, 3, 20m), CancellationToken.None);

        Assert.Single(repo.Stored);
        Assert.Equal(repo.Stored[0].Id, result.Id);
        Assert.Equal(1, uow.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivateItemReorderLevelHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repo = new FakeItemReorderLevelRepository();
        var uow = new FakeUnitOfWork();
        var handler = new DeactivateItemReorderLevelHandler(repo, uow);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateItemReorderLevelCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivateItemReorderLevelHandler_HappyPath_DeactivatesAndSaves()
    {
        var repo = new FakeItemReorderLevelRepository();
        var uow = new FakeUnitOfWork();
        var handler = new DeactivateItemReorderLevelHandler(repo, uow);
        var entity = new ItemReorderLevel(1, 2, 10m);
        entity.Id = 5;
        await repo.AddAsync(entity);

        await handler.Handle(new DeactivateItemReorderLevelCommand(5), CancellationToken.None);

        Assert.False(repo.Stored[0].IsActive);
        Assert.Equal(1, uow.SaveCalledCount);
    }

    [Fact]
    public async Task GetItemReorderLevelHandler_GetById_ReturnsDto()
    {
        var repo = new FakeItemReorderLevelRepository();
        var handler = new GetItemReorderLevelHandler(repo);
        var entity = new ItemReorderLevel(1, 2, 10m, 3, 20m);
        entity.Id = 7;
        await repo.AddAsync(entity);

        var dto = await handler.Handle(new GetItemReorderLevelQuery(7), CancellationToken.None);

        Assert.NotNull(dto);
        Assert.Equal(7, dto!.Id);
        Assert.Equal(1, dto.CompanyId);
    }

    [Fact]
    public async Task GetItemReorderLevelHandler_GetByCompany_ReturnsList()
    {
        var repo = new FakeItemReorderLevelRepository();
        var handler = new GetItemReorderLevelHandler(repo);
        var e1 = new ItemReorderLevel(1, 2, 10m);
        var e2 = new ItemReorderLevel(1, 3, 5m);
        e1.Id = 1;
        e2.Id = 2;
        await repo.AddAsync(e1);
        await repo.AddAsync(e2);

        var list = await handler.Handle(new GetItemReorderLevelsByCompanyQuery(1), CancellationToken.None);

        Assert.Equal(2, list.Count);
    }
}
