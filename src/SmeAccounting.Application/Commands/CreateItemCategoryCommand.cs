using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateItemCategoryCommand(
    long CompanyId,
    string Code,
    string Name,
    long? ParentId = null,
    string? Description = null) : IRequest<CreateItemCategoryResult>;

public record CreateItemCategoryResult(long Id);
