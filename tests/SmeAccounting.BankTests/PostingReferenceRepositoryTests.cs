using SmeAccounting.Domain.Entities;

namespace SmeAccounting.BankTests;

public sealed class PostingReferenceRepositoryTests
{
    [Fact]
    public async Task GetBySourceAsync_EmptyStore_ReturnsNull()
    {
        var repo = new FakePostingReferenceRepository();

        var found = await repo.GetBySourceAsync("OpeningBalance", 9, 1);

        Assert.Null(found);
    }

    [Fact]
    public async Task GetBySourceAsync_AfterAdd_TripleMatchReturnsRow()
    {
        var repo = new FakePostingReferenceRepository();
        await repo.AddAsync(new PostingReference(1, 7, "OpeningBalance", 9));

        var found = await repo.GetBySourceAsync("OpeningBalance", 9, 1);
        var miss = await repo.GetBySourceAsync("OpeningBalance", 9, 2);

        Assert.NotNull(found);
        Assert.Equal(1, found.CompanyId);
        Assert.Null(miss);
    }
}
