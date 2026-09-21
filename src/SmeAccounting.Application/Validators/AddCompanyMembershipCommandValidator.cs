using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class AddCompanyMembershipCommandValidator : AbstractValidator<AddCompanyMembershipCommand>
{
    public AddCompanyMembershipCommandValidator()
    {
        RuleFor(x => x.UserId).GreaterThan(0);
        RuleFor(x => x.CompanyId).GreaterThan(0);
    }
}
