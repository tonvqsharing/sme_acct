namespace SmeAccounting.Application.DTOs;
public record InventoryValuationPolicyDto(long Id, long CompanyId, string Code, string Name, string ValuationMethod, bool IsActive, string? Description);
