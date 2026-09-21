namespace SmeAccounting.Application.DTOs;

public record UserDto(long Id, string ExternalId, string Email, string DisplayName, string? UserName, bool IsActive);
