using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetCompanySettingByIdQuery(long Id) : IRequest<CompanySettingDto?>;
