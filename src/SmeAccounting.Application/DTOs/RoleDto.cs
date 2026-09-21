namespace SmeAccounting.Application.DTOs;

public record RoleDto(long Id, long CompanyId, string Code, string Name, string? Description, bool IsActive);
