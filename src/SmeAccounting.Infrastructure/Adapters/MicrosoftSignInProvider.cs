namespace SmeAccounting.Infrastructure.Adapters;

public interface IMicrosoftSignInProvider
{
    Task<bool> ValidateTokenAsync(string token, CancellationToken cancellationToken = default);
    Task<string?> GetExternalIdAsync(string token, CancellationToken cancellationToken = default);
}

public class MicrosoftSignInProvider : IMicrosoftSignInProvider
{
    // Placeholder implementation for Microsoft Entra ID sign-in integration
    public Task<bool> ValidateTokenAsync(string token, CancellationToken cancellationToken = default)
    {
        // TODO: integrate Microsoft.Identity.Web token validation
        return Task.FromResult(!string.IsNullOrWhiteSpace(token));
    }

    public Task<string?> GetExternalIdAsync(string token, CancellationToken cancellationToken = default)
    {
        // TODO: extract object identifier from Microsoft token claims
        return Task.FromResult<string?>(null);
    }
}
