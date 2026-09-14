namespace SmeAccounting.Infrastructure.Storage;

public interface IFileStorage
{
    Task<string> SaveFileAsync(Stream fileStream, string fileName, string contentType, CancellationToken cancellationToken = default);
    Task<Stream> GetFileAsync(string path, CancellationToken cancellationToken = default);
    Task<bool> DeleteFileAsync(string path, CancellationToken cancellationToken = default);
}
