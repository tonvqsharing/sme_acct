using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.BankTests;

public sealed class CreateJournalEntryHandlerTests
{
    private static readonly DateTimeOffset TestDate = new(2026, 9, 23, 0, 0, 0, TimeSpan.Zero);

    private static CreateJournalEntryCommand ValidCommand() =>
        new(1, TestDate, 1, "Test entry", null, null,
            [new JournalEntryLineInput(101, 10m, 0m, null), new JournalEntryLineInput(102, 0m, 10m, null)]);

    [Fact]
    public async Task CreateJournalEntryValidator_Valid_Passes()
    {
        var validator = new CreateJournalEntryCommandValidator();
        var result = await validator.ValidateAsync(ValidCommand());

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task CreateJournalEntryValidator_CompanyIdZero_Fails()
    {
        var validator = new CreateJournalEntryCommandValidator();
        var result = await validator.ValidateAsync(ValidCommand() with { CompanyId = 0 });

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateJournalEntryValidator_PeriodIdZero_Fails()
    {
        var validator = new CreateJournalEntryCommandValidator();
        var result = await validator.ValidateAsync(ValidCommand() with { PeriodId = 0 });

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateJournalEntryValidator_EmptyLines_Fails()
    {
        var validator = new CreateJournalEntryCommandValidator();
        var result = await validator.ValidateAsync(ValidCommand() with { Lines = [] });

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreateJournalEntryHandler_HappyPath_FormatsEntryNumberAndSaves()
    {
        var voucherTypeRepo = new FakeVoucherTypeRepository();
        await voucherTypeRepo.AddAsync(new VoucherType(1, "JNRL", "Journal", VoucherCategory.Journal));
        var seriesRepo = new FakeDocumentNumberingSeriesRepository();
        await seriesRepo.AddAsync(new DocumentNumberingSeries(1, voucherTypeRepo.Stored[0].Id, "JNRL", paddingLength: 6, isDefault: true));
        var journalEntryRepo = new FakeJournalEntryRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateJournalEntryHandler(voucherTypeRepo, seriesRepo, journalEntryRepo, unitOfWork);

        var result = await handler.Handle(ValidCommand(), CancellationToken.None);

        Assert.Equal("JNRL000001", journalEntryRepo.Stored[0].EntryNumber);
        Assert.Equal("JNRL000001", result.EntryNumber);
        Assert.Equal(2, seriesRepo.Stored[0].NextNumber);
        Assert.Equal(journalEntryRepo.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task CreateJournalEntryHandler_MissingVoucherType_Throws()
    {
        var voucherTypeRepo = new FakeVoucherTypeRepository();
        var seriesRepo = new FakeDocumentNumberingSeriesRepository();
        var journalEntryRepo = new FakeJournalEntryRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateJournalEntryHandler(voucherTypeRepo, seriesRepo, journalEntryRepo, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => handler.Handle(ValidCommand(), CancellationToken.None));
    }

    [Fact]
    public async Task CreateJournalEntryHandler_MissingDefaultSeries_Throws()
    {
        var voucherTypeRepo = new FakeVoucherTypeRepository();
        await voucherTypeRepo.AddAsync(new VoucherType(1, "JNRL", "Journal", VoucherCategory.Journal));
        var seriesRepo = new FakeDocumentNumberingSeriesRepository();
        var journalEntryRepo = new FakeJournalEntryRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateJournalEntryHandler(voucherTypeRepo, seriesRepo, journalEntryRepo, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => handler.Handle(ValidCommand(), CancellationToken.None));
    }
}