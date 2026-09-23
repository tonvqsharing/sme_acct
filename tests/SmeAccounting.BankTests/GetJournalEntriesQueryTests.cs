using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.BankTests;

public sealed class GetJournalEntriesQueryTests
{
    private static readonly DateTimeOffset TestDate = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);

    [Fact]
    public async Task Handle_ReturnsAllEntries_InInsertionOrder_WithLinesMapped()
    {
        var repo = new FakeJournalEntryRepository();
        var first = new JournalEntry("JE-1", TestDate, 1, "First entry");
        first.AddLine(101, new Money(10m, "VND"), new Money(0m, "VND"));
        first.AddLine(102, new Money(0m, "VND"), new Money(10m, "VND"));
        var second = new JournalEntry("JE-2", TestDate.AddDays(1), 1, "Second entry");
        second.AddLine(201, new Money(5m, "VND"), new Money(0m, "VND"));
        second.AddLine(202, new Money(0m, "VND"), new Money(5m, "VND"));
        await repo.AddAsync(first);
        await repo.AddAsync(second);

        var handler = new GetJournalEntriesQueryHandler(repo);
        var result = await handler.Handle(new GetJournalEntriesQuery(), CancellationToken.None);

        Assert.Equal(2, result.Count);
        Assert.Equal("JE-1", result[0].EntryNumber);
        Assert.Equal("First entry", result[0].Description);
        Assert.Equal("JE-2", result[1].EntryNumber);
        Assert.Equal(2, result[0].Lines.Count);
        Assert.Equal(101, result[0].Lines[0].AccountId);
        Assert.Equal(10m, result[0].Lines[0].Debit.Amount);
        Assert.Equal("VND", result[0].Lines[0].Debit.Currency);
        Assert.Equal(10m, result[0].Lines[1].Credit.Amount);
    }

    [Fact]
    public async Task Handle_WhenNoEntries_ReturnsEmptyList()
    {
        var handler = new GetJournalEntriesQueryHandler(new FakeJournalEntryRepository());
        var result = await handler.Handle(new GetJournalEntriesQuery(), CancellationToken.None);
        Assert.Empty(result);
    }

    [Fact]
    public async Task Handle_MapsPostedState()
    {
        var repo = new FakeJournalEntryRepository();
        var entry = new JournalEntry("JE-1", TestDate, 1);
        entry.AddLine(101, new Money(10m, "VND"), new Money(0m, "VND"));
        entry.AddLine(102, new Money(0m, "VND"), new Money(10m, "VND"));
        entry.Post("tester", TestDate);
        await repo.AddAsync(entry);

        var handler = new GetJournalEntriesQueryHandler(repo);
        var result = await handler.Handle(new GetJournalEntriesQuery(), CancellationToken.None);

        Assert.True(result[0].IsPosted);
        Assert.NotNull(result[0].PostedAt);
    }
}