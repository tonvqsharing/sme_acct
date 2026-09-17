namespace SmeAccounting.Application.DTOs;

public record EmployeeDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string? EmployeeNumber,
    string? TaxCode,
    string? Address,
    string? Phone,
    string? Email,
    DateOnly? HireDate,
    bool IsActive,
    string? Description);
