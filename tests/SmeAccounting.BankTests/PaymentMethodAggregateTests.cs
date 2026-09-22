using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.BankTests;

public sealed class PaymentMethodAggregateTests
{
    [Fact]
    public void PaymentMethod_Ctor_Valid_RaisesPaymentMethodCreatedWithCompanyId()
    {
        var method = new PaymentMethod(1, "CASH", "Cash", PaymentMethodCategory.Cash);

        Assert.Equal(1, method.CompanyId);
        Assert.Equal("CASH", method.Code);
        Assert.True(method.IsActive);
        Assert.False(method.RequiresBankAccount);
        var evt = Assert.Single(method.DomainEvents.OfType<PaymentMethodCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void PaymentMethod_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PaymentMethod(0, "CASH", "Cash", PaymentMethodCategory.Cash));
    }

    [Fact]
    public void PaymentMethod_Ctor_CompanyIdNegative_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PaymentMethod(-1, "CASH", "Cash", PaymentMethodCategory.Cash));
    }

    [Fact]
    public void PaymentMethod_Ctor_EmptyCode_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PaymentMethod(1, string.Empty, "Cash", PaymentMethodCategory.Cash));
    }

    [Fact]
    public void PaymentMethod_Ctor_EmptyName_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new PaymentMethod(1, "CASH", "  ", PaymentMethodCategory.Cash));
    }

    [Fact]
    public void PaymentMethod_Deactivate_SetsIsActiveFalse()
    {
        var method = new PaymentMethod(1, "CASH", "Cash", PaymentMethodCategory.Cash);

        method.Deactivate();

        Assert.False(method.IsActive);
    }

    [Fact]
    public void PaymentMethod_Ctor_RequiresBankAccountTrue_Persisted()
    {
        var method = new PaymentMethod(1, "BT", "Bank Transfer", PaymentMethodCategory.BankTransfer, requiresBankAccount: true);

        Assert.True(method.RequiresBankAccount);
    }

    [Fact]
    public void CreatePaymentMethodValidator_Valid_Passes()
    {
        var validator = new CreatePaymentMethodCommandValidator();
        var result = validator.Validate(new CreatePaymentMethodCommand(1, "CASH", "Cash", PaymentMethodCategory.Cash));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreatePaymentMethodValidator_CompanyIdZero_Fails()
    {
        var validator = new CreatePaymentMethodCommandValidator();
        var result = validator.Validate(new CreatePaymentMethodCommand(0, "CASH", "Cash", PaymentMethodCategory.Cash));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreatePaymentMethodValidator_EmptyCode_Fails()
    {
        var validator = new CreatePaymentMethodCommandValidator();
        var result = validator.Validate(new CreatePaymentMethodCommand(1, string.Empty, "Cash", PaymentMethodCategory.Cash));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreatePaymentMethodValidator_EmptyName_Fails()
    {
        var validator = new CreatePaymentMethodCommandValidator();
        var result = validator.Validate(new CreatePaymentMethodCommand(1, "CASH", string.Empty, PaymentMethodCategory.Cash));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreatePaymentMethodValidator_BadCategory_Fails()
    {
        var validator = new CreatePaymentMethodCommandValidator();
        var result = validator.Validate(new CreatePaymentMethodCommand(1, "CASH", "Cash", (PaymentMethodCategory)999));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void CreatePaymentMethodValidator_OverLength_Fails()
    {
        var validator = new CreatePaymentMethodCommandValidator();

        Assert.False(validator.Validate(new CreatePaymentMethodCommand(1, new string('X', 21), "Cash", PaymentMethodCategory.Cash)).IsValid);
        Assert.False(validator.Validate(new CreatePaymentMethodCommand(1, "CASH", new string('X', 201), PaymentMethodCategory.Cash)).IsValid);
        Assert.False(validator.Validate(new CreatePaymentMethodCommand(1, "CASH", "Cash", PaymentMethodCategory.Cash, Description: new string('X', 501))).IsValid);
    }

    [Fact]
    public async Task CreatePaymentMethodHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakePaymentMethodRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreatePaymentMethodHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreatePaymentMethodCommand(1, "CASH", "Cash", PaymentMethodCategory.Cash), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal("CASH", repository.Stored[0].Code);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }
}
