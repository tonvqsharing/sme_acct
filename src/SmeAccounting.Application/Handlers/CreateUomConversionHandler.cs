using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateUomConversionHandler(
    IUomConversionRepository repository,
    IUomRepository uomRepository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateUomConversionCommand, CreateUomConversionResult>
{
    public async Task<CreateUomConversionResult> Handle(CreateUomConversionCommand request, CancellationToken cancellationToken)
    {
        var fromUom = await uomRepository.GetByIdAsync(request.FromUomId);
        var toUom = await uomRepository.GetByIdAsync(request.ToUomId);
        if (fromUom?.UomClassId is not null && toUom?.UomClassId is not null && fromUom.UomClassId != toUom.UomClassId)
            throw new DomainException("Cannot convert between UOMs of different classes.");

        var conv = new UomConversion(request.CompanyId, request.FromUomId, request.ToUomId, request.Factor);
        await repository.AddAsync(conv);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateUomConversionResult(conv.Id);
    }
}