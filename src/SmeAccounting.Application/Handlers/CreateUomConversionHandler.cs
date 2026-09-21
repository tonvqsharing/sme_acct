using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateUomConversionHandler(
    IUomConversionRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateUomConversionCommand, CreateUomConversionResult>
{
    public async Task<CreateUomConversionResult> Handle(CreateUomConversionCommand request, CancellationToken cancellationToken)
    {
        var conv = new UomConversion(request.CompanyId, request.FromUomId, request.ToUomId, request.Factor);
        await repository.AddAsync(conv);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateUomConversionResult(conv.Id);
    }
}
