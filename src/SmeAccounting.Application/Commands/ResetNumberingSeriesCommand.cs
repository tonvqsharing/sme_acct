using MediatR;

namespace SmeAccounting.Application.Commands;

public record ResetNumberingSeriesCommand(long SeriesId, int StartFrom) : IRequest<ResetNumberingSeriesResult>;

public record ResetNumberingSeriesResult;
