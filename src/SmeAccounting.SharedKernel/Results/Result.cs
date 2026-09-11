namespace SmeAccounting.SharedKernel;

public class Result
{
    protected Result(bool isSuccess, IReadOnlyCollection<Failure> failures)
    {
        IsSuccess = isSuccess;
        _failures = failures;
    }

    private readonly IReadOnlyCollection<Failure> _failures;

    public bool IsSuccess { get; }

    public bool IsFailure => !IsSuccess;

    public IReadOnlyCollection<Failure> Failures => _failures;

    public static Result Success() => new(true, []);

    public static Result Fail(Failure failure) => new(false, [failure]);

    public static Result Fail(IEnumerable<Failure> failures) => new(false, failures.ToArray());

    public static Result Fail(string code, string description) => new(false, [new Failure(code, description)]);

    public static implicit operator Result(Failure failure) => Fail(failure);
}