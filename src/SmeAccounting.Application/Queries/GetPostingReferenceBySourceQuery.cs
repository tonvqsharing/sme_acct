using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetPostingReferenceBySourceQuery(string SourceType, long SourceId, long CompanyId) : IRequest<PostingReferenceDto?>;
