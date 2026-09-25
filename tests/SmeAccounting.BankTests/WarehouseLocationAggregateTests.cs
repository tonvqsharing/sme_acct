using SmeAccounting.Application.Commands;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Queries;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class WarehouseLocationAggregateTests
{
    [Fact]
    public void WarehouseLocation_Ctor_Valid_RaisesWarehouseLocationCreatedWithCompanyId()
    {
        var entity = new WarehouseLocation(1, 2, "LOC01", "Location One", "Description");

        Assert.Equal(1, entity.CompanyId);
        Assert.Equal(2, entity.WarehouseId);
        Assert.Equal("LOC01", entity.Code);
        Assert.Equal("Location One", entity.Name);
        Assert.Equal("Description", entity.Description);
        Assert.True(entity.IsActive);
        var evt = Assert.Single(entity.DomainEvents.OfType<WarehouseLocationCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void WarehouseLocation_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new WarehouseLocation(0, 2, "LOC01", "Location One"));
    }

    [Fact]
    public void WarehouseLocation_Ctor_WarehouseIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new WarehouseLocation(1, 0, "LOC01", "Location One"));
    }

    [Fact]
    public void WarehouseLocation_Ctor_CodeEmpty_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new WarehouseLocation(1, 2, "", "Location One"));
    }

    [Fact]
    public void WarehouseLocation_Ctor_CodeWhitespace_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new WarehouseLocation(1, 2, "   ", "Location One"));
    }

    [Fact]
    public void WarehouseLocation_Ctor_NameEmpty_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new WarehouseLocation(1, 2, "LOC01", ""));
    }

    [Fact]
    public void WarehouseLocation_Deactivate_SetsIsActiveFalse()
    {
        var entity = new WarehouseLocation(1, 2, "LOC01", "Location One");
        entity.Deactivate();
        Assert.False(entity.IsActive);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_Valid_Passes()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(1, 2, "LOC01", "Location One", "Desc"));
        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(0, 2, "LOC01", "Location One"));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_WarehouseIdZero_Fails()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(1, 0, "LOC01", "Location One"));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_CodeEmpty_Fails()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(1, 2, "", "Location One"));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_CodeTooLong_Fails()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(1, 2, new string('A', 21), "Location One"));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_NameEmpty_Fails()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(1, 2, "LOC01", ""));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_NameTooLong_Fails()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(1, 2, "LOC01", new string('A', 201)));
        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateWarehouseLocationValidator_DescriptionTooLong_Fails()
    {
        var validator = new CreateWarehouseLocationCommandValidator();
        var result = validator.Validate(new CreateWarehouseLocationCommand(1, 2, "LOC01", "Location One", new string('A', 501)));
        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateWarehouseLocationHandler_HappyPath_AddsAndSaves()
    {
        var repo = new FakeWarehouseLocationRepository();
        var uow = new FakeUnitOfWork();
        var handler = new CreateWarehouseLocationHandler(repo, uow);

        var result = await handler.Handle(new CreateWarehouseLocationCommand(1, 2, "LOC01", "Location One", "Desc"), CancellationToken.None);

        Assert.Single(repo.Stored);
        Assert.Equal(repo.Stored[0].Id, result.Id);
        Assert.Equal(1, uow.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivateWarehouseLocationHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repo = new FakeWarehouseLocationRepository();
        var uow = new FakeUnitOfWork();
        var handler = new DeactivateWarehouseLocationHandler(repo, uow);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateWarehouseLocationCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivateWarehouseLocationHandler_HappyPath_DeactivatesAndSaves()
    {
        var repo = new FakeWarehouseLocationRepository();
        var uow = new FakeUnitOfWork();
        var handler = new DeactivateWarehouseLocationHandler(repo, uow);

        var entity = new WarehouseLocation(1, 2, "LOC01", "Location One");
        entity.Id = 5;
        await repo.AddAsync(entity);

        await handler.Handle(new DeactivateWarehouseLocationCommand(5), CancellationToken.None);

        Assert.False(repo.Stored[0].IsActive);
        Assert.Equal(1, uow.SaveCalledCount);
    }

    [Fact]
    public async Task GetWarehouseLocationHandler_GetById_ReturnsDto()
    {
        var repo = new FakeWarehouseLocationRepository();
        var handler = new GetWarehouseLocationHandler(repo);
        var entity = new WarehouseLocation(1, 2, "LOC01", "Location One", "Desc");
        entity.Id = 7;
        await repo.AddAsync(entity);

        var dto = await handler.Handle(new GetWarehouseLocationQuery(7), CancellationToken.None);

        Assert.NotNull(dto);
        Assert.Equal(7, dto!.Id);
        Assert.Equal(1, dto.CompanyId);
        Assert.Equal(2, dto.WarehouseId);
        Assert.Equal("LOC01", dto.Code);
    }

    [Fact]
    public async Task GetWarehouseLocationHandler_GetByCompany_ReturnsList()
    {
        var repo = new FakeWarehouseLocationRepository();
        var handler = new GetWarehouseLocationHandler(repo);

        var entity1 = new WarehouseLocation(1, 2, "LOC01", "Location One");
        entity1.Id = 8;
        await repo.AddAsync(entity1);

        var entity2 = new WarehouseLocation(2, 3, "LOC02", "Location Two");
        entity2.Id = 9;
        await repo.AddAsync(entity2);

        var dtos = await handler.Handle(new GetWarehouseLocationsByCompanyQuery(1), CancellationToken.None);

        Assert.Single(dtos);
        Assert.Equal(1, dtos[0].CompanyId);
    }
}