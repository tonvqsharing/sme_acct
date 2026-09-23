using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.BankTests;

public sealed class PostJournalEntryHandlerTests
{
    private static readonly DateTimeOffset TestDate = new(2026, 9, 23, 0, 0, 0, TimeSpan.Zero);

    private static JournalEntry BalancedEntry()
    {
        var entry = new JournalEntry("JE-1", TestDate, 1);
        entry.AddLine(101, new Money(10m, "VND"), new Money(0m, "VND"));
        entry.AddLine(102, new Money(0m, "VND"), new Money(10m, "VND"));
        return entry;
    }

    [Fact]
    public async Task PostJournalEntryValidator_JournalEntryIdZero_Fails()
    {
        var validator = new PostJournalEntryCommandValidator();
        var result = await validator.ValidateAsync(new PostJournalEntryCommand(0));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task PostJournalEntryHandler_HappyPath_PostsAndSaves()
    {
        var journalEntryRepo = new FakeJournalEntryRepository();
        var entry = BalancedEntry();
        await journalEntryRepo.AddAsync(entry);
        var unitOfWork = new FakeUnitOfWork();
        var clock = new FakeClock { Now = TestDate };
        var handler = new PostJournalEntryHandler(journalEntryRepo, unitOfWork, clock);

        var result = await handler.Handle(new PostJournalEntryCommand(entry.Id), CancellationToken.None);

        Assert.True(journalEntryRepo.Stored[0].IsPosted);
        Assert.Equal(clock.Now, journalEntryRepo.Stored[0].PostedAt);
        Assert.Equal("system", journalEntryRepo.Stored[0].PostedBy);
        Assert.Equal(entry.Id, result.JournalEntryId);
        Assert.Equal(clock.Now, result.PostedAt);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task PostJournalEntryHandler_AlreadyPosted_Throws()
    {
        var journalEntryRepo = new FakeJournalEntryRepository();
        var entry = BalancedEntry();
        await journalEntryRepo.AddAsync(entry);
        var unitOfWork = new FakeUnitOfWork();
        var clock = new FakeClock { Now = TestDate };
        var handler = new PostJournalEntryHandler(journalEntryRepo, unitOfWork, clock);

        await handler.Handle(new PostJournalEntryCommand(entry.Id), CancellationToken.None);

        var ex = await Assert.ThrowsAsync<DomainException>(
            () => handler.Handle(new PostJournalEntryCommand(entry.Id), CancellationToken.None));
        Assert.Equal("Journal entry is already posted.", ex.Message);
    }

    [Fact]
    public async Task PostJournalEntryHandler_NotFound_Throws()
    {
        var journalEntryRepo = new FakeJournalEntryRepository();
        var unitOfWork = new FakeUnitOfWork();
        var clock = new FakeClock { Now = TestDate };
        var handler = new PostJournalEntryHandler(journalEntryRepo, unitOfWork, clock);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => handler.Handle(new PostJournalEntryCommand(999), CancellationToken.None));
    }
}