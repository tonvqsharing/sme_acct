using FluentValidation;
using SmeAccounting.Modules.Authorization.Application.Commands;

namespace SmeAccounting.Modules.Authorization.Application.Validators;

public sealed class CreateRoleCommandValidator : AbstractValidator<CreateRoleCommand>
{
    public CreateRoleCommandValidator()
    {
        RuleFor(x => x.RoleName)
            .NotEmpty()
            .MaximumLength(256)
            .Matches("^[A-Za-z0-9_.-]+$");
    }
}
