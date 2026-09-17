using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateDocumentNumberingSeriesCommand(
    long VoucherTypeId,
    long CompanyId,
    string Prefix,
    int PaddingLength,
    bool IsDefault,
    string? Description = null) : IRequest<CreateDocumentNumberingSeriesResult>;

public record CreateDocumentNumberingSeriesResult(long Id);
