using MediatR; using SmeAccounting.Application.DTOs;
namespace SmeAccounting.Application.Queries;
public record GetInventoryAccountingConfigurationQuery(long Id) : IRequest<InventoryAccountingConfigurationDto?>;
public record GetInventoryAccountingConfigurationByCompanyQuery(long CompanyId) : IRequest<InventoryAccountingConfigurationDto?>;
