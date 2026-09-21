namespace SmeAccounting.Application.DTOs;

public record ServiceItemDto(long Id, long CompanyId, string Code, string Name, long? UomId, bool IsActive, string? Description);
