using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetSupplierQuery(long SupplierId) : IRequest<SupplierDto?>;
