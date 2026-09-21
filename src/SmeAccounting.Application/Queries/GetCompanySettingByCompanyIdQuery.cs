using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetCompanySettingByCompanyIdQuery(long CompanyId) : IRequest<CompanySettingDto?>;
