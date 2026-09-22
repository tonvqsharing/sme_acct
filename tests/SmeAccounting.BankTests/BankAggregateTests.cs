using SmeAccounting.Application.Banks.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class BankAggregateTests
{
    [Fact]
    public void Bank_Ctor_Valid_RaisesBankCreatedWithCompanyId()
    {
        var bank = new Bank(1, "VCB", "Vietcombank");

        Assert.Equal(1, bank.CompanyId);
        Assert.Equal("VCB", bank.Code);
        Assert.True(bank.IsActive);
        var evt = Assert.Single(bank.DomainEvents.OfType<BankCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void Bank_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new Bank(0, "VCB", "Vietcombank"));
    }

    [Fact]
    public void Bank_Ctor_EmptyCode_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new Bank(1, string.Empty, "Vietcombank"));
    }

    [Fact]
    public void Bank_Ctor_EmptyName_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new Bank(1, "VCB", "  "));
    }

    [Fact]
    public void Bank_Deactivate_SetsIsActiveFalse()
    {
        var bank = new Bank(1, "VCB", "Vietcombank");

        bank.Deactivate();

        Assert.False(bank.IsActive);
    }

    [Fact]
    public void BankBranch_Ctor_Valid_RaisesBankBranchCreated()
    {
        var branch = new BankBranch(1, 7, "HN", "Ha Noi Branch");

        Assert.Equal(1, branch.CompanyId);
        Assert.Equal(7, branch.BankId);
        Assert.True(branch.IsActive);
        var evt = Assert.Single(branch.DomainEvents.OfType<BankBranchCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void BankBranch_Ctor_BankIdZero_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new BankBranch(1, 0, "HN", "Ha Noi Branch"));
    }

    [Fact]
    public void BankAccount_Ctor_Valid_RaisesBankAccountCreated()
    {
        var account = new BankAccount(1, 7, "VND", "0011001234567", "VCB VND Account");

        Assert.Equal(1, account.CompanyId);
        Assert.Equal(7, account.BankId);
        Assert.True(account.IsActive);
        var evt = Assert.Single(account.DomainEvents.OfType<BankAccountCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void BankAccount_Ctor_EmptyAccountNumber_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new BankAccount(1, 7, "VND", string.Empty, "VCB VND Account"));
    }

    [Fact]
    public void BankAccount_Ctor_EmptyAccountName_ThrowsDomainException()
    {
        Assert.Throws<DomainException>(() => new BankAccount(1, 7, "VND", "0011001234567", " "));
    }

    [Fact]
    public void CreateBankValidator_Valid_Passes()
    {
        var validator = new CreateBankCommandValidator();
        var result = validator.Validate(new CreateBankCommand(1, "VCB", "Vietcombank"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public void CreateBankValidator_EmptyCode_Fails()
    {
        var validator = new CreateBankCommandValidator();
        var result = validator.Validate(new CreateBankCommand(1, string.Empty, "Vietcombank"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateBankHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakeBankRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateBankCommandHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreateBankCommand(1, "VCB", "Vietcombank"), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }
}
