using FluentValidation;
using MediatR;
using NSubstitute;
using SmeAccounting.Application.Behaviours;

namespace SmeAccounting.Application.Tests;

public class ValidationBehaviourTests
{
    [Fact]
    public async Task Handle_NoValidators_CallsNext()
    {
        var next = Substitute.For<RequestHandlerDelegate<string>>();
        next().Returns("result");

        var behaviour = new ValidationBehaviour<TestRequest, string>(Enumerable.Empty<IValidator<TestRequest>>());

        var result = await behaviour.Handle(new TestRequest(), next, CancellationToken.None);

        Assert.Equal("result", result);
        await next.Received(1)();
    }

    [Fact]
    public async Task Handle_ValidRequest_CallsNext()
    {
        var validator = Substitute.For<IValidator<TestRequest>>();
        var validationResult = new FluentValidation.Results.ValidationResult();
        validator.ValidateAsync(Arg.Any<ValidationContext<TestRequest>>(), Arg.Any<CancellationToken>())
            .Returns(validationResult);

        var next = Substitute.For<RequestHandlerDelegate<string>>();
        next().Returns("result");

        var behaviour = new ValidationBehaviour<TestRequest, string>(new[] { validator });

        var result = await behaviour.Handle(new TestRequest(), next, CancellationToken.None);

        Assert.Equal("result", result);
    }

    [Fact]
    public async Task Handle_InvalidRequest_ThrowsValidationException()
    {
        var validator = Substitute.For<IValidator<TestRequest>>();
        var failures = new List<FluentValidation.Results.ValidationFailure>
        {
            new("Name", "Name is required")
        };
        var validationResult = new FluentValidation.Results.ValidationResult(failures);
        validator.ValidateAsync(Arg.Any<ValidationContext<TestRequest>>(), Arg.Any<CancellationToken>())
            .Returns(validationResult);

        var next = Substitute.For<RequestHandlerDelegate<string>>();

        var behaviour = new ValidationBehaviour<TestRequest, string>(new[] { validator });

        await Assert.ThrowsAsync<FluentValidation.ValidationException>(
            () => behaviour.Handle(new TestRequest(), next, CancellationToken.None));
    }

    public record TestRequest : IRequest<string>;
}
