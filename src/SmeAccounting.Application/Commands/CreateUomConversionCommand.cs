using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateUomConversionCommand(
    long CompanyId,
    long FromUomId,
    long ToUomId,
    decimal Factor) : IRequest<CreateUomConversionResult>;

public record CreateUomConversionResult(long Id);
