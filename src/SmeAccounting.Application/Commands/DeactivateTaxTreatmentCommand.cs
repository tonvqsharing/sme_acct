using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateTaxTreatmentCommand(long TaxTreatmentId) : IRequest<DeactivateTaxTreatmentResult>;

public record DeactivateTaxTreatmentResult;
