using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.BankTests;

public sealed class JournalEntrySourceTests
{
    private static readonly DateTimeOffset TestDate = new(2026, 1, 1, 0, 0, 0, TimeSpan.Zero);

    private static JournalEntry NewBalancedPostedEntry()
    {
        var entry = new JournalEntry("JE-1", TestDate, 1);
        entry.AddLine(101, new Money(10m, "VND"), new Money(0m, "VND"));
        entry.AddLine(102, new Money(0m, "VND"), new Money(10m, "VND"));
        entry.Post("tester", TestDate);
        return entry;
    }

    private static OpeningBalancePeriod NewBalancedPeriod()
    {
        var period = new OpeningBalancePeriod(1, 1, new DateOnly(2026, 1, 1));
        period.AddEntry(101, new Money(10m, "VND"), new Money(0m, "VND"));
        period.AddEntry(102, new Money(0m, "VND"), new Money(10m, "VND"));
        return period;
    }

    // (a) happy — valid SetSource sets SourceType and SourceId.
    [Fact]
    public void SetSource_Valid_SetsPropsAndDoesNotThrow()
    {
        var entry = new JournalEntry("JE-1", TestDate, 1);

        entry.SetSource("OpeningBalance", 9);

        Assert.Equal("OpeningBalance", entry.SourceType);
        Assert.Equal(9, entry.SourceId);
    }

    // (b) empty type — null / "" / "  " each throw DomainException with "SourceType is required."
    [Fact]
    public void SetSource_EmptySourceType_ThrowsDomainException()
    {
        var entry = new JournalEntry("JE-1", TestDate, 1);

        foreach (var sourceType in new string?[] { null, string.Empty, "  " })
        {
            var ex = Assert.Throws<DomainException>(() => entry.SetSource(sourceType!, 9));

            Assert.Equal("SourceType is required.", ex.Message);
        }
    }

    // (c) zero + negative sourceId — each throw DomainException with "SourceId must be greater than zero."
    [Fact]
    public void SetSource_SourceIdZeroOrNegative_ThrowsDomainException()
    {
        var entry = new JournalEntry("JE-1", TestDate, 1);

        foreach (var sourceId in new long[] { 0, -1 })
        {
            var ex = Assert.Throws<DomainException>(() => entry.SetSource("OpeningBalance", sourceId));

            Assert.Equal("SourceId must be greater than zero.", ex.Message);
        }
    }

    // (d) SetSource after Post throws DomainException with "Cannot modify a posted journal entry."
    [Fact]
    public void SetSource_AfterPost_ThrowsDomainException()
    {
        var entry = NewBalancedPostedEntry();

        var ex = Assert.Throws<DomainException>(() => entry.SetSource("OpeningBalance", 9));

        Assert.Equal("Cannot modify a posted journal entry.", ex.Message);
    }

    // (e) SetSource before Post on an unposted JE does not throw.
    [Fact]
    public void SetSource_BeforePost_OnUnpostedEntry_DoesNotThrow()
    {
        var entry = new JournalEntry("JE-1", TestDate, 1);

        entry.SetSource("OpeningBalance", 9);
        entry.AddLine(101, new Money(10m, "VND"), new Money(0m, "VND"));
        entry.AddLine(102, new Money(0m, "VND"), new Money(10m, "VND"));
        entry.Post("tester", TestDate);

        Assert.True(entry.IsPosted);
        Assert.Equal("OpeningBalance", entry.SourceType);
    }

    // (f) transient period (Id == 0, never-saved) post throws DomainException with the caller fail-fast message.
    [Fact]
    public void PostOpeningBalances_TransientPeriod_IdZero_ThrowsDomainException()
    {
        var period = NewBalancedPeriod();
        Assert.Equal(0, period.Id);

        var ex = Assert.Throws<DomainException>(() => period.PostOpeningBalances("tester", TestDate));

        Assert.Equal("Cannot post opening balances before the period is persisted.", ex.Message);
        Assert.False(period.IsPosted);
        Assert.Equal(PeriodStatus.Open, period.Status);
    }

    // (g) persisted-Id path unchanged — real Id passes through SetSource with no behavior change.
    [Fact]
    public void PostOpeningBalances_PersistedPeriod_RealId_PostsUnchanged()
    {
        var period = NewBalancedPeriod();
        period.Id = 5;

        period.PostOpeningBalances("tester", TestDate);

        Assert.True(period.IsPosted);
        Assert.Equal(PeriodStatus.Closed, period.Status);
        var evt = Assert.Single(period.DomainEvents.OfType<OpeningBalancesPosted>());
        Assert.Equal(5, evt.PeriodId);
    }

    // (G2-1) PostOpeningBalances returns the created JE — non-null, source-traced, posted.
    [Fact]
    public void PostOpeningBalances_ReturnsJournalEntry_SourceAndPosted()
    {
        var period = NewBalancedPeriod();
        period.Id = 5;

        var journalEntry = period.PostOpeningBalances("tester", TestDate);

        Assert.NotNull(journalEntry);
        Assert.Equal("OpeningBalance", journalEntry.SourceType);
        Assert.Equal(period.Id, journalEntry.SourceId);
        Assert.True(journalEntry.IsPosted);
    }

    // (G2-2) returned JE carries the balanced lines built from the period entries.
    [Fact]
    public void PostOpeningBalances_ReturnsJournalEntry_BalancedLines()
    {
        var period = NewBalancedPeriod();
        period.Id = 5;

        var journalEntry = period.PostOpeningBalances("tester", TestDate);

        Assert.Equal(2, journalEntry.Lines.Count);
        Assert.Equal(
            journalEntry.Lines.Sum(l => l.Debit.Amount),
            journalEntry.Lines.Sum(l => l.Credit.Amount));
    }

    // (G2-3) returned JE is transient (Id == 0) — domain never persists; G3 handler Add+Save assigns Id.
    [Fact]
    public void PostOpeningBalances_ReturnsJournalEntry_TransientIdZero()
    {
        var period = NewBalancedPeriod();
        period.Id = 5;

        var journalEntry = period.PostOpeningBalances("tester", TestDate);

        Assert.Equal(0, journalEntry.Id);
    }

    // (h) handler persists period flags — FakeUnitOfWork.SaveCalledCount == 1.
    [Fact]
    public async Task PostOpeningBalancesHandler_PersistsPeriodFlags_SaveCalledOnce()
    {
        var periodRepository = new FakeOpeningBalancePeriodRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new PostOpeningBalancesHandler(periodRepository, unitOfWork);
        var period = NewBalancedPeriod();
        await periodRepository.AddAsync(period);
        period.Id = 1;

        var result = await handler.Handle(new PostOpeningBalancesCommand(1, "tester", TestDate), CancellationToken.None);

        Assert.True(result.Success);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
        Assert.True(period.IsPosted);
        Assert.Equal(PeriodStatus.Closed, period.Status);
    }

    // (i) JE discard recorded — handler has zero IJournalEntryRepository (assert-and-record; never asserting JE persisted).
    [Fact]
    public void PostOpeningBalancesHandler_DiscardsJournalEntry_NoJournalEntryRepository()
    {
        var parameters = typeof(PostOpeningBalancesHandler)
            .GetConstructors()
            .Single()
            .GetParameters();

        Assert.DoesNotContain(parameters, p => p.ParameterType == typeof(IJournalEntryRepository));
    }
}
