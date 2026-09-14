using Microsoft.Extensions.Options;
using SmeAccounting.Infrastructure.Options;

namespace SmeAccounting.Infrastructure.Storage;

public class LocalFileStorage : IFileStorage
{
    private readonly string _basePath;
    
    public LocalFileStorage(IOptions<SecurityOptions> options)
    {
        _basePath = Path.Combine(options.Value.DataProtectionPath, "..", "uploads");
        Directory.CreateDirectory(_basePath);
    }
    
    public async Task<string> SaveFileAsync(Stream fileStream, string fileName, string contentType, CancellationToken cancellationToken = default)
    {
        var uniqueName = $"{Guid.NewGuid():N}_{Path.GetFileName(fileName)}";
        var path = Path.Combine(_basePath, uniqueName);
        
        await using var fileOutput = File.Create(path);
        await fileStream.CopyToAsync(fileOutput, cancellationToken);
        
        return uniqueName;
    }
    
    public Task<Stream> GetFileAsync(string path, CancellationToken cancellationToken = default)
    {
        var fullPath = Path.Combine(_basePath, path);
        if (!File.Exists(fullPath))
            throw new FileNotFoundException($"File not found: {path}");
        
        return Task.FromResult<Stream>(File.OpenRead(fullPath));
    }
    
    public Task<bool> DeleteFileAsync(string path, CancellationToken cancellationToken = default)
    {
        var fullPath = Path.Combine(_basePath, path);
        if (File.Exists(fullPath))
        {
            File.Delete(fullPath);
            return Task.FromResult(true);
        }
        return Task.FromResult(false);
    }
}
