using SmeAccounting.Modules.Identity.Domain;

namespace SmeAccounting.Modules.Identity.Infrastructure;

public static class ApplicationUserMapper
{
    public static User ToDomain(ApplicationUser appUser)
    {
        var user = (User)Activator.CreateInstance(typeof(User), nonPublic: true)!;
        user.Id = appUser.Id;
        user.DisplayName = appUser.DisplayName;
        user.Email = appUser.Email!;
        user.UserName = appUser.UserName!;
        user.BranchId = appUser.BranchId;
        user.IsEnabled = appUser.IsEnabled;
        user.CreatedAtUtc = appUser.CreatedAtUtc;
        user.LastLoginAtUtc = appUser.LastLoginAtUtc;
        return user;
    }

    public static Role ToDomain(ApplicationRole appRole)
    {
        var role = (Role)Activator.CreateInstance(typeof(Role), nonPublic: true)!;
        role.Id = appRole.Id;
        role.Name = appRole.Name!;
        role.NormalizedName = appRole.NormalizedName!;
        role.Description = appRole.Description;
        role.DisplayOrder = appRole.DisplayOrder;
        return role;
    }
}
