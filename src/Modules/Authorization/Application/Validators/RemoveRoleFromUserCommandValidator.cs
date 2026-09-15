using FluentValidation;
using SmeAccounting.Modules.Authorization.Application.Commands;

namespace SmeAccounting.Modules.Authorization.Application.Validators;

public sealed class RemoveRoleFromUserCommandValidator : AbstractValidator<RemoveRoleFromUserCommand>
{
    public RemoveRoleFromUserCommandValidator()
    {
        RuleFor(x => x.UserId).NotEmpty();

        RuleFor(x => x.RoleName)
            .NotEmpty()
            .MaximumLength(256)
            .Matches("^[A-Za-z0-9_.-]+$");
    }
}
