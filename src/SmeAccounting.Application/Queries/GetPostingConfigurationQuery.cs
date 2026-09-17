using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetPostingConfigurationQuery(long ConfigId) : IRequest<PostingConfigurationDto?>;
