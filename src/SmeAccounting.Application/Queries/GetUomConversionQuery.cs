using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetUomConversionQuery(long Id) : IRequest<UomConversionDto?>;

public record GetUomConversionsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<UomConversionDto>>;
