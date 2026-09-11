namespace SmeAccounting.SharedKernel;

public abstract class ValueObject : IEquatable<ValueObject>
{
    protected abstract IEnumerable<object> GetAtomicValues();

    public override bool Equals(object? obj) => obj is ValueObject other && Equals(other);

    public bool Equals(ValueObject? other) => other is not null && ValuesAreEqual(other);

    private bool ValuesAreEqual(ValueObject other) => GetAtomicValues().SequenceEqual(other.GetAtomicValues());

    public override int GetHashCode() =>
        GetAtomicValues().Aggregate(17, (acc, value) => acc * 31 + (value?.GetHashCode() ?? 0));

    public static bool operator ==(ValueObject? left, ValueObject? right) => left is null ? right is null : left.Equals(right);

    public static bool operator !=(ValueObject? left, ValueObject? right) => !(left == right);
}