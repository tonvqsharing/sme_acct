using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetPostingConfigurationsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<PostingConfigurationDto>>;
