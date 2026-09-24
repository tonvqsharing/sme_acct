using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemBarcodeQuery(long Id) : IRequest<ItemBarcodeDto?>;

public record GetItemBarcodesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemBarcodeDto>>;