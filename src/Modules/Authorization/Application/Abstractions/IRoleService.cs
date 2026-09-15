using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Abstractions;

public interface IRoleService
{
    Task<Result> CreateAsync(string roleName, string? description, CancellationToken cancellationToken = default);

    Task<Result> DeleteAsync(string roleName, CancellationToken cancellationToken = default);

    Task<Result> AssignPermissionAsync(string roleName, string permission, CancellationToken cancellationToken = default);

    Task<Result> RevokePermissionAsync(string roleName, string permission, CancellationToken cancellationToken = default);

    Task<Result> AssignRoleToUserAsync(Guid userId, string roleName, CancellationToken cancellationToken = default);

    Task<Result> RemoveRoleFromUserAsync(Guid userId, string roleName, CancellationToken cancellationToken = default);

    Task<Result<IReadOnlyList<string>>> GetRolePermissionsAsync(string roleName, CancellationToken cancellationToken = default);

    Task<Result<IReadOnlyList<string>>> ListRolesAsync(CancellationToken cancellationToken = default);
}
