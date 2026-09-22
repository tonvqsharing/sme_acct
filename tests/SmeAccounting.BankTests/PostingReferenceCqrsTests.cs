using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Application.Queries;
using SmeAccounting.Application.Validators;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.BankTests;

public sealed class PostingReferenceCqrsTests
{
    [Fact]
    public async Task CreatePostingReferenceValidator_Valid_Passes()
    {
        var validator = new CreatePostingReferenceCommandValidator();
        var result = await validator.ValidateAsync(new CreatePostingReferenceCommand(1, 7, "OpeningBalance", 9));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task CreatePostingReferenceValidator_CompanyIdZero_Fails()
    {
        var validator = new CreatePostingReferenceCommandValidator();
        var result = await validator.ValidateAsync(new CreatePostingReferenceCommand(0, 7, "OpeningBalance", 9));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreatePostingReferenceValidator_JournalEntryIdZero_Fails()
    {
        var validator = new CreatePostingReferenceCommandValidator();
        var result = await validator.ValidateAsync(new CreatePostingReferenceCommand(1, 0, "OpeningBalance", 9));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreatePostingReferenceValidator_EmptySourceType_Fails()
    {
        var validator = new CreatePostingReferenceCommandValidator();

        Assert.False((await validator.ValidateAsync(new CreatePostingReferenceCommand(1, 7, string.Empty, 9))).IsValid);
        Assert.False((await validator.ValidateAsync(new CreatePostingReferenceCommand(1, 7, "  ", 9))).IsValid);
    }

    [Fact]
    public async Task CreatePostingReferenceValidator_SourceIdZero_Fails()
    {
        var validator = new CreatePostingReferenceCommandValidator();
        var result = await validator.ValidateAsync(new CreatePostingReferenceCommand(1, 7, "OpeningBalance", 0));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreatePostingReferenceValidator_SourceType101Chars_Fails()
    {
        var validator = new CreatePostingReferenceCommandValidator();
        var result = await validator.ValidateAsync(new CreatePostingReferenceCommand(1, 7, new string('x', 101), 9));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task CreatePostingReferenceHandler_HappyPath_AddsAndSaves()
    {
        var repository = new FakePostingReferenceRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreatePostingReferenceHandler(repository, unitOfWork);

        var result = await handler.Handle(new CreatePostingReferenceCommand(1, 7, "OpeningBalance", 9), CancellationToken.None);

        Assert.Single(repository.Stored);
        Assert.Equal("OpeningBalance", repository.Stored[0].SourceType);
        Assert.Equal(repository.Stored[0].Id, result.Id);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task CreatePostingReferenceHandler_DuplicateTriple_Throws()
    {
        var repository = new FakePostingReferenceRepository();
        var unitOfWork = new FakeUnitOfWork();
        await repository.AddAsync(new PostingReference(1, 7, "OpeningBalance", 9));
        var handler = new CreatePostingReferenceHandler(repository, unitOfWork);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => handler.Handle(new CreatePostingReferenceCommand(1, 7, "OpeningBalance", 9), CancellationToken.None));

        Assert.Single(repository.Stored);
    }

    [Fact]
    public async Task GetPostingReferenceByIdHandler_NullPassthrough()
    {
        var repository = new FakePostingReferenceRepository();
        var handler = new GetPostingReferenceByIdHandler(repository);

        Assert.Null(await handler.Handle(new GetPostingReferenceByIdQuery(1), CancellationToken.None));

        await repository.AddAsync(new PostingReference(1, 7, "OpeningBalance", 9));

        var dto = await handler.Handle(new GetPostingReferenceByIdQuery(0), CancellationToken.None);

        Assert.NotNull(dto);
        Assert.Equal(1, dto.CompanyId);
        Assert.Equal(7, dto.JournalEntryId);
        Assert.Equal("OpeningBalance", dto.SourceType);
        Assert.Equal(9, dto.SourceId);
    }

    [Fact]
    public async Task GetPostingReferenceBySourceHandler_NullPassthrough()
    {
        var repository = new FakePostingReferenceRepository();
        var handler = new GetPostingReferenceBySourceHandler(repository);

        Assert.Null(await handler.Handle(new GetPostingReferenceBySourceQuery("OpeningBalance", 9, 1), CancellationToken.None));

        await repository.AddAsync(new PostingReference(1, 7, "OpeningBalance", 9));

        var dto = await handler.Handle(new GetPostingReferenceBySourceQuery("OpeningBalance", 9, 1), CancellationToken.None);

        Assert.NotNull(dto);
        Assert.Equal(1, dto.CompanyId);
        Assert.Equal("OpeningBalance", dto.SourceType);
        Assert.Null(await handler.Handle(new GetPostingReferenceBySourceQuery("OpeningBalance", 9, 2), CancellationToken.None));
    }
}
