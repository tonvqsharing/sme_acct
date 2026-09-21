using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateUomConversionCommand(long Id) : IRequest<DeactivateUomConversionResult>;

public record DeactivateUomConversionResult(bool Success);
