using SmeAccounting.SharedKernel;

namespace SmeAccounting.Domain.Tests;

public class BaseEntityTests
{
    [Fact]
    public void BaseEntity_Id_DefaultsToZero()
    {
        var entity = new TestEntity();

        Assert.Equal(0, entity.Id);
    }

    [Fact]
    public void BaseEntity_CanSetId()
    {
        var entity = new TestEntity();
        entity.Id = 42;

        Assert.Equal(42, entity.Id);
    }

    [Fact]
    public void BaseEntity_DomainEvents_InitiallyEmpty()
    {
        var entity = new TestEntity();

        Assert.Empty(entity.DomainEvents);
    }

    [Fact]
    public void BaseEntity_RaiseDomainEvent_AddsToCollection()
    {
        var entity = new TestEntity();
        entity.RaiseTestEvent();

        Assert.Single(entity.DomainEvents);
    }

    [Fact]
    public void BaseEntity_ClearDomainEvents_EmptiesCollection()
    {
        var entity = new TestEntity();
        entity.RaiseTestEvent();
        entity.ClearDomainEvents();

        Assert.Empty(entity.DomainEvents);
    }

    private sealed class TestEntity : BaseEntity
    {
        public void RaiseTestEvent() => RaiseDomainEvent(new TestDomainEvent());
    }

    private sealed record TestDomainEvent : IDomainEvent
    {
        public DateTime OccurredAtUtc { get; init; } = DateTime.UtcNow;
    }
}
