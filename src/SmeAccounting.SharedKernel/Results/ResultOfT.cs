namespace SmeAccounting.SharedKernel;

public class Result<T> : Result
{
    private readonly T? _value;

    private Result(T value) : base(true, []) => _value = value;

    private Result(Failure failure) : base(false, [failure]) => _value = default;

    public T? Value =>
        IsSuccess
            ? _value
            : throw new InvalidOperationException("Cannot access the Value of a failed Result.");

    public static Result<T> Create(T value) => new(value);

    public static new Result<T> Fail(Failure failure) => new(failure);

    public static new Result<T> Fail(string code, string description) => new(new Failure(code, description));

    public static implicit operator Result<T>(T value) => Create(value);

    public static implicit operator Result<T>(Failure failure) => Fail(failure);
}