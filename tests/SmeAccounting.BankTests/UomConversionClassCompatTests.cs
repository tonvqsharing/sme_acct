using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Handlers;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.BankTests;

public sealed class UomConversionClassCompatTests
{
    [Fact]
    public async Task CreateUomConversionHandler_BothClassesDiffer_ThrowsDomainException()
    {
        var uomRepository = new FakeUomRepository();
        var fromUom = new Uom(1, "KG", "Kilogram", uomClassId: 1);
        fromUom.Id = 5;
        var toUom = new Uom(1, "BOX", "Box", uomClassId: 2);
        toUom.Id = 6;
        await uomRepository.AddAsync(fromUom);
        await uomRepository.AddAsync(toUom);
        var conversionRepository = new FakeUomConversionRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateUomConversionHandler(conversionRepository, uomRepository, unitOfWork);

        await Assert.ThrowsAsync<DomainException>(() => handler.Handle(new CreateUomConversionCommand(1, 5, 6, 2m), CancellationToken.None));

        Assert.Empty(conversionRepository.Stored);
        Assert.Equal(0, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task CreateUomConversionHandler_BothSameClass_Allowed()
    {
        var uomRepository = new FakeUomRepository();
        var fromUom = new Uom(1, "KG", "Kilogram", uomClassId: 1);
        fromUom.Id = 5;
        var toUom = new Uom(1, "G", "Gram", uomClassId: 1);
        toUom.Id = 6;
        await uomRepository.AddAsync(fromUom);
        await uomRepository.AddAsync(toUom);
        var conversionRepository = new FakeUomConversionRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateUomConversionHandler(conversionRepository, uomRepository, unitOfWork);

        var result = await handler.Handle(new CreateUomConversionCommand(1, 5, 6, 1000m), CancellationToken.None);

        Assert.Single(conversionRepository.Stored);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
        Assert.Equal(conversionRepository.Stored[0].Id, result.Id);
    }

    [Fact]
    public async Task CreateUomConversionHandler_OneUnclassified_Allowed()
    {
        var uomRepository = new FakeUomRepository();
        var fromUom = new Uom(1, "KG", "Kilogram");
        fromUom.Id = 5;
        var toUom = new Uom(1, "BOX", "Box", uomClassId: 1);
        toUom.Id = 6;
        await uomRepository.AddAsync(fromUom);
        await uomRepository.AddAsync(toUom);
        var conversionRepository = new FakeUomConversionRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateUomConversionHandler(conversionRepository, uomRepository, unitOfWork);

        await handler.Handle(new CreateUomConversionCommand(1, 5, 6, 2m), CancellationToken.None);

        Assert.Single(conversionRepository.Stored);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }

    [Fact]
    public async Task CreateUomConversionHandler_BothUnclassified_Allowed()
    {
        var uomRepository = new FakeUomRepository();
        var fromUom = new Uom(1, "KG", "Kilogram");
        fromUom.Id = 5;
        var toUom = new Uom(1, "G", "Gram");
        toUom.Id = 6;
        await uomRepository.AddAsync(fromUom);
        await uomRepository.AddAsync(toUom);
        var conversionRepository = new FakeUomConversionRepository();
        var unitOfWork = new FakeUnitOfWork();
        var handler = new CreateUomConversionHandler(conversionRepository, uomRepository, unitOfWork);

        await handler.Handle(new CreateUomConversionCommand(1, 5, 6, 1000m), CancellationToken.None);

        Assert.Single(conversionRepository.Stored);
        Assert.Equal(1, unitOfWork.SaveCalledCount);
    }
}