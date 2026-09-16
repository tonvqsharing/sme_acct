namespace SmeAccounting.Infrastructure.Adapters;

public class EInvoiceProviderAdapter
{
    public Task<object> SubmitAsync(object request, CancellationToken ct = default)
    {
        throw new NotImplementedException("E-invoice TVAN provider integration — architecture placeholder.");
    }
}
