using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class PostingReferenceAggregateTests
{
    [Fact]
    public void PostingReference_Ctor_Valid_SetsPropsAndRaisesSingleCreatedEvent()
    {
        var reference = new PostingReference(1, 7, "OpeningBalance", 9);

        Assert.Equal(1, reference.CompanyId);
        Assert.Equal(7, reference.JournalEntryId);
        Assert.Equal("OpeningBalance", reference.SourceType);
        Assert.Equal(9, reference.SourceId);
        var evt = Assert.Single(reference.DomainEvents.OfType<PostingReferenceCreated>());
        Assert.Equal(1, evt.CompanyId);
    }

    [Fact]
    public void PostingReference_Ctor_CompanyIdZero_ThrowsDomainException()
    {
        var ex = Assert.Throws<DomainException>(() => new PostingReference(0, 7, "OpeningBalance", 9));

        Assert.Equal("CompanyId must be greater than zero.", ex.Message);
    }

    [Fact]
    public void PostingReference_Ctor_JournalEntryIdZero_ThrowsDomainException()
    {
        var ex = Assert.Throws<DomainException>(() => new PostingReference(1, 0, "OpeningBalance", 9));

        Assert.Equal("JournalEntryId must be greater than zero.", ex.Message);
    }

    [Fact]
    public void PostingReference_Ctor_EmptySourceType_ThrowsDomainException()
    {
        foreach (var sourceType in new string?[] { null, string.Empty, "  " })
        {
            var ex = Assert.Throws<DomainException>(() => new PostingReference(1, 7, sourceType!, 9));

            Assert.Equal("SourceType is required.", ex.Message);
        }
    }

    [Fact]
    public void PostingReference_Ctor_SourceIdZero_ThrowsDomainException()
    {
        var ex = Assert.Throws<DomainException>(() => new PostingReference(1, 7, "OpeningBalance", 0));

        Assert.Equal("SourceId must be greater than zero.", ex.Message);
    }

    [Fact]
    public void PostingReferenceCreated_Event_Payload_Minimal()
    {
        var reference = new PostingReference(1, 7, "OpeningBalance", 9);

        var evt = Assert.Single(reference.DomainEvents);
        var created = Assert.IsType<PostingReferenceCreated>(evt);
        Assert.Equal(1, created.CompanyId);
        var propNames = typeof(PostingReferenceCreated).GetProperties().Select(p => p.Name).ToHashSet();
        Assert.DoesNotContain("SourceType", propNames);
        Assert.DoesNotContain("SourceId", propNames);
        Assert.DoesNotContain("JournalEntryId", propNames);
    }
}
