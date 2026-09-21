using MediatR;
namespace SmeAccounting.Application.Commands;
public record CreateServiceItemCommand(long CompanyId, string Code, string Name, long? UomId = null, string? Description = null) : IRequest<CreateServiceItemResult>;
public record CreateServiceItemResult(long Id);
