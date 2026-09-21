namespace SmeAccounting.Application.DTOs;

public record UomConversionDto(
    long Id,
    long CompanyId,
    long FromUomId,
    long ToUomId,
    decimal Factor,
    bool IsActive);
