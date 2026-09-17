using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateEmployeeCommand(long EmployeeId) : IRequest<DeactivateEmployeeResult>;

public record DeactivateEmployeeResult;
