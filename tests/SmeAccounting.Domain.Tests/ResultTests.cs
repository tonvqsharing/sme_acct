using SmeAccounting.SharedKernel;

namespace SmeAccounting.Domain.Tests;

public class ResultTests
{
    [Fact]
    public void Success_ReturnsSuccessfulResult()
    {
        var result = Result.Success();

        Assert.True(result.IsSuccess);
        Assert.Empty(result.Failures);
    }

    [Fact]
    public void Success_WithValue_ReturnsSuccessfulResult()
    {
        var result = Result<string>.Create("test");

        Assert.True(result.IsSuccess);
        Assert.Equal("test", result.Value);
    }

    [Fact]
    public void Fail_WithFailure_ReturnsFailedResult()
    {
        var failure = new Failure("TEST_ERROR", "Test error message");
        var result = Result.Fail(failure);

        Assert.False(result.IsSuccess);
        Assert.Single(result.Failures);
        Assert.Equal("TEST_ERROR", result.Failures.First().Code);
    }

    [Fact]
    public void Fail_WithCodeAndDescription_ReturnsFailedResult()
    {
        var result = Result.Fail("TEST_ERROR", "Test message");

        Assert.False(result.IsSuccess);
        Assert.Equal("TEST_ERROR", result.Failures.First().Code);
        Assert.Equal("Test message", result.Failures.First().Description);
    }

    [Fact]
    public void Result_ImplicitConversion_FromValue()
    {
        Result<string> result = "hello";

        Assert.True(result.IsSuccess);
        Assert.Equal("hello", result.Value);
    }

    [Fact]
    public void Result_ImplicitConversion_FromFailure()
    {
        Result<string> result = new Failure("CODE", "msg");

        Assert.False(result.IsSuccess);
    }

    [Fact]
    public void Result_ThrowOnValueAccess_WhenFailed()
    {
        Result<int> result = new Failure("CODE", "msg");

        Assert.Throws<InvalidOperationException>(() => _ = result.Value);
    }

    [Fact]
    public void Result_T_Fail_WithCodeAndDescription_ReturnsFailedResult()
    {
        var result = Result<int>.Fail("CODE", "msg");

        Assert.False(result.IsSuccess);
        Assert.Equal("CODE", result.Failures.First().Code);
    }
}
