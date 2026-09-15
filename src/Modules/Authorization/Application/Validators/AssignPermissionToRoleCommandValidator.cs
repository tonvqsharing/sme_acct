using FluentValidation;
using SmeAccounting.Modules.Authorization.Application.Commands;
using SmeAccounting.Modules.Authorization.Domain;

namespace SmeAccounting.Modules.Authorization.Application.Validators;

public sealed class AssignPermissionToRoleCommandValidator : AbstractValidator<AssignPermissionToRoleCommand>
{
    public AssignPermissionToRoleCommandValidator()
    {
        RuleFor(x => x.RoleName)
            .NotEmpty()
            .MaximumLength(256)
            .Matches("^[A-Za-z0-9_.-]+$");

        RuleFor(x => x.Permission)
            .NotEmpty()
            .Must(p => Permissions.All.Contains(p))
            .WithMessage("Permission must be a known permission.");
    }
}
