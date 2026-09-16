namespace SmeAccounting.Infrastructure.Adapters;

public class DigitalSignatureAdapter
{
    public Task<byte[]> SignAsync(byte[] data, CancellationToken ct = default)
    {
        throw new NotImplementedException("Digital signature HSM/USB token integration — architecture placeholder.");
    }
}
