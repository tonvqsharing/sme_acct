using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateSupplierCommand(
    long CompanyId,
    string Code,
    string Name,
    string? TaxCode = null,
    string? Address = null,
    string? Phone = null,
    string? Email = null,
    long? PaymentTermId = null,
    long? DefaultTaxTypeId = null,
    string? Description = null) : IRequest<CreateSupplierResult>;

public record CreateSupplierResult(long Id);
