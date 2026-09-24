using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Queries;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class ItemGroupAggregateTests
{
    [Fact]
    public void ItemGroup_Ctor_Valid_RaisesItemGroupCreatedWithCompanyId()
    {
        var group = new ItemGroup(1, "GRP1", "Group One");

        Assert.Equal(1, group.CompanyId);
        Assert.Equal("GRP1", group.Code);
        Assert.True(group.IsActive);
        var evt = Assert.Single(group.DomainEvents.OfType<ItemGroupCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void ItemGroup_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemGroup(0, "GRP1", "Group One"));
    }

    [Fact]
    public void ItemGroup_Ctor_CompanyIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemGroup(-1, "GRP1", "Group One"));
    }

    [Fact]
    public void ItemGroup_Ctor_EmptyCode_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemGroup(1, string.Empty, "Group One"));
    }

    [Fact]
    public void ItemGroup_Ctor_EmptyName_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new ItemGroup(1, "GRP1", "  "));
    }

    [Fact]
    public void ItemGroup_Deactivate_SetsIsActiveFalse()
    {
        var group = new ItemGroup(1, "GRP1", "Group One");

        group.Deactivate();

        Assert.False(group.IsActive);
    }

    [Fact]
    public void CreateItemGroupValidator_Valid_Passes()
    {
        var validator = new CreateItemGroupCommandValidator();
        var result = validator.Validate(new CreateItemGroupCommand(1, "GRP1", "Group One"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateItemGroupValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateItemGroupCommandValidator();
        var result = validator.Validate(new CreateItemGroupCommand(0, "GRP1", "Group One"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemGroupValidator_EmptyCode_Fails()
    {
        var validator = new CreateItemGroupCommandValidator();
        var result = validator.Validate(new CreateItemGroupCommand(1, string.Empty, "Group One"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemGroupValidator_EmptyName_Fails()
    {
        var validator = new CreateItemGroupCommandValidator();
        var result = validator.Validate(new CreateItemGroupCommand(1, "GRP1", string.Empty));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateItemGroupValidator_OverLength_Fails()
    {
        var validator = new CreateItemGroupCommandValidator();

        Assert.False(validator.Validate(new CreateItemGroupCommand(1, new string('X', 21), "Group One")).IsValid);
        Assert.False(validator.Validate(new CreateItemGroupCommand(1, "GRP1", new string('X', 201))).IsValid);
        Assert.False(validator.Validate(new CreateItemGroupCommand(1, "GRP1", "Group One", Description: new string('X', 501))).IsValid);
    }

    [Fact]
    public async Task CreateItemGroupHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakeItemGroupRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateItemGroupHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreateItemGroupCommand(1, "GRP1", "Group One"), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal("GRP1", repository.Stored[0].Code);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivateItemGroupHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repository = new FakeItemGroupRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemGroupHandler(repository, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateItemGroupCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivateItemGroupHandler_HappyPath_DeactivatesAndSaves()
    {
        var repository = new FakeItemGroupRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateItemGroupHandler(repository, unitOfWork);
        var group = new ItemGroup(1, "GRP1", "Group One");
        group.Id = 5;
        await repository.AddAsync(group);

        await handler.Handle(new DeactivateItemGroupCommand(5), CancellationToken.None);

        Assert.False(repository.Stored[0].IsActive);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task GetItemGroupRepository_GetAllByCompany_ReturnsOnlyRequestedCompany()
    {
        var repository = new FakeItemGroupRepository();
        await repository.AddAsync(new ItemGroup(1, "GRP1", "Group One"));
        await repository.AddAsync(new ItemGroup(2, "GRP2", "Group Two"));

        var result = await repository.GetAllByCompanyAsync(1);

        Assert.Single(result);
        Assert.Equal("GRP1", result[0].Code);
    }

    [Fact]
    public void Item_Ctor_ItemGroupIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new Item(1, "ITM1", "Item One", false, true, itemGroupId: 0));
    }

    [Fact]
    public void Item_Ctor_ItemGroupIdSet_AssignsItemGroupId()
    {
        var item = new Item(1, "ITM1", "Item One", false, true, itemGroupId: 5);

        Assert.Equal(5, item.ItemGroupId);
    }

    [Fact]
    public void CreateItemValidator_ItemGroupIdZero_FailsWhenPresent()
    {
        var validator = new CreateItemCommandValidator();

        Assert.False(validator.Validate(new CreateItemCommand(1, "ITM1", "Item One", false, true, ItemGroupId: 0)).IsValid);
        Assert.True(validator.Validate(new CreateItemCommand(1, "ITM1", "Item One", false, true)).IsValid);
    }

    [Fact]
    public async Task GetItemHandler_Map_IncludesItemGroupId()
    {
        var repository = new FakeItemRepository();
        var item = new Item(1, "ITM1", "Item One", false, true, itemGroupId: 5);
        item.Id = 5;
        await repository.AddAsync(item);
        var handler = new GetItemHandler(repository);

        var result = await handler.Handle(new GetItemQuery(5), CancellationToken.None);

        Assert.Equal(5, result!.ItemGroupId);
    }
}