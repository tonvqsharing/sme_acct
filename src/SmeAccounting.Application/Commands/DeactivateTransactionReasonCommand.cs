using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTransactionReasonCommand(long ReasonId) : IRequest<DeactivateTransactionReasonResult>;

public record DeactivateTransactionReasonResult;
