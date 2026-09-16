using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.ArchitectureTests;

public class PostingRuleIsolationTests
{
    [Fact]
    public void IPostingService_Should_Reside_In_Domain_Assembly()
    {
        var type = typeof(IPostingService);
        Assert.Equal(typeof(Account).Assembly, type.Assembly);
    }

    [Fact]
    public void JournalEntry_Balance_Rule_Should_Be_Enforceable_In_Domain()
    {
        var journalEntryType = typeof(JournalEntry);
        Assert.NotNull(journalEntryType);
        Assert.Equal(typeof(Account).Assembly, journalEntryType.Assembly);

        var moneyType = typeof(Money);
        Assert.NotNull(moneyType);
        Assert.Equal(typeof(Account).Assembly, moneyType.Assembly);

        var postingServiceType = typeof(IPostingService);
        Assert.NotNull(postingServiceType);
        Assert.Equal(typeof(Account).Assembly, postingServiceType.Assembly);
    }
}
