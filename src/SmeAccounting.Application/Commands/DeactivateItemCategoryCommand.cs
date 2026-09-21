using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemCategoryCommand(long Id) : IRequest<DeactivateItemCategoryResult>;

public record DeactivateItemCategoryResult(bool Success);
