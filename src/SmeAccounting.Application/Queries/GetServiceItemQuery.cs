using MediatR;
using SmeAccounting.Application.DTOs;
namespace SmeAccounting.Application.Queries;
public record GetServiceItemQuery(long Id) : IRequest<ServiceItemDto?>;
public record GetServiceItemsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ServiceItemDto>>;
