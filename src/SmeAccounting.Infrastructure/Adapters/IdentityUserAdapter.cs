using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Adapters;

// Placeholder mapping to ASP.NET Core Identity user model without hard package dependency
public record IdentityUserModel(string Id, string UserName, string Email, bool EmailConfirmed);

public class IdentityUserAdapter
{
    public static IdentityUserModel ToIdentityUser(User user)
    {
        return new IdentityUserModel(
            Id: user.Id.ToString(),
            UserName: user.UserName ?? user.Email,
            Email: user.Email,
            EmailConfirmed: false
        );
    }

    public static User ToDomainUser(IdentityUserModel identityUser)
    {
        var externalId = identityUser.Id;
        var displayName = !string.IsNullOrWhiteSpace(identityUser.UserName) ? identityUser.UserName : identityUser.Email;
        var userName = identityUser.UserName;
        return new User(externalId, identityUser.Email, displayName, userName);
    }
}
