using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Queries;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class UomClassAggregateTests
{
    [Fact]
    public void UomClass_Ctor_Valid_RaisesUomClassCreatedWithCompanyId()
    {
        var uomClass = new UomClass(1, "WEIGHT", "Weight Class");

        Assert.Equal(1, uomClass.CompanyId);
        Assert.Equal("WEIGHT", uomClass.Code);
        Assert.True(uomClass.IsActive);
        var evt = Assert.Single(uomClass.DomainEvents.OfType<UomClassCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void UomClass_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new UomClass(0, "WEIGHT", "Weight Class"));
    }

    [Fact]
    public void UomClass_Ctor_CompanyIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new UomClass(-1, "WEIGHT", "Weight Class"));
    }

    [Fact]
    public void UomClass_Ctor_EmptyCode_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new UomClass(1, string.Empty, "Weight Class"));
    }

    [Fact]
    public void UomClass_Ctor_EmptyName_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new UomClass(1, "WEIGHT", "  "));
    }

    [Fact]
    public void UomClass_Deactivate_SetsIsActiveFalse()
    {
        var uomClass = new UomClass(1, "WEIGHT", "Weight Class");

        uomClass.Deactivate();

        Assert.False(uomClass.IsActive);
    }

    [Fact]
    public void CreateUomClassValidator_Valid_Passes()
    {
        var validator = new CreateUomClassCommandValidator();
        var result = validator.Validate(new CreateUomClassCommand(1, "WEIGHT", "Weight Class"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateUomClassValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateUomClassCommandValidator();
        var result = validator.Validate(new CreateUomClassCommand(0, "WEIGHT", "Weight Class"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateUomClassValidator_EmptyCode_Fails()
    {
        var validator = new CreateUomClassCommandValidator();
        var result = validator.Validate(new CreateUomClassCommand(1, string.Empty, "Weight Class"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateUomClassValidator_EmptyName_Fails()
    {
        var validator = new CreateUomClassCommandValidator();
        var result = validator.Validate(new CreateUomClassCommand(1, "WEIGHT", string.Empty));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateUomClassValidator_OverLength_Fails()
    {
        var validator = new CreateUomClassCommandValidator();

        Assert.False(validator.Validate(new CreateUomClassCommand(1, new string('X', 21), "Weight Class")).IsValid);
        Assert.False(validator.Validate(new CreateUomClassCommand(1, "WEIGHT", new string('X', 201))).IsValid);
        Assert.False(validator.Validate(new CreateUomClassCommand(1, "WEIGHT", "Weight Class", Description: new string('X', 501))).IsValid);
    }

    [Fact]
    public async Task CreateUomClassHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakeUomClassRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateUomClassHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreateUomClassCommand(1, "WEIGHT", "Weight Class"), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal("WEIGHT", repository.Stored[0].Code);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task DeactivateUomClassHandler_MissingEntity_ThrowsInvalidOperationException()
    {
        var repository = new FakeUomClassRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateUomClassHandler(repository, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(() => handler.Handle(new DeactivateUomClassCommand(999), CancellationToken.None));
    }

    [Fact]
    public async Task DeactivateUomClassHandler_HappyPath_DeactivatesAndSaves()
    {
        var repository = new FakeUomClassRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new DeactivateUomClassHandler(repository, unitOfWork);
        var uomClass = new UomClass(1, "WEIGHT", "Weight Class");
        uomClass.Id = 5;
        await repository.AddAsync(uomClass);

        await handler.Handle(new DeactivateUomClassCommand(5), CancellationToken.None);

        Assert.False(repository.Stored[0].IsActive);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task GetAllByCompanyAsync_FiltersByCompany()
    {
        var repository = new FakeUomClassRepository();
        await repository.AddAsync(new UomClass(1, "WEIGHT", "Weight Class"));
        await repository.AddAsync(new UomClass(2, "VOLUME", "Volume Class"));

        var result = await repository.GetAllByCompanyAsync(1);

        Assert.Single(result);
        Assert.Equal("WEIGHT", result[0].Code);
    }

    [Fact]
    public void Uom_Ctor_UomClassIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new Uom(1, "KG", "Kilogram", uomClassId: 0));
    }

    [Fact]
    public void Uom_Ctor_UomClassIdFive_SetsProperty()
    {
        var uom = new Uom(1, "KG", "Kilogram", uomClassId: 5);

        Assert.Equal(5, uom.UomClassId);
    }

    [Fact]
    public void CreateUomCommandValidator_UomClassIdZero_FailsWhenPresent()
    {
        var validator = new CreateUomCommandValidator();
        var result = validator.Validate(new CreateUomCommand(1, "KG", "Kilogram", UomClassId: 0));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreateUomCommandValidator_UomClassIdNull_Passes()
    {
        var validator = new CreateUomCommandValidator();
        var result = validator.Validate(new CreateUomCommand(1, "KG", "Kilogram"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task GetUomHandler_Map_IncludesUomClassId()
    {
        var repository = new FakeUomRepository();
        var uom = new Uom(1, "KG", "Kilogram", uomClassId: 5);
        uom.Id = 5;
        await repository.AddAsync(uom);
        var handler = new GetUomHandler(repository);

        var dto = await handler.Handle(new GetUomQuery(5), CancellationToken.None);

        Assert.NotNull(dto);
        Assert.Equal(5, dto!.UomClassId);
    }
}