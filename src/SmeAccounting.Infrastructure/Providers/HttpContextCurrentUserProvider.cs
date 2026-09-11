namespace SmeAccounting.Infrastructure.Providers;

using System.Security.Claims;
using Microsoft.AspNetCore.Http;
using SmeAccounting.SharedKernel;

public sealed class HttpContextCurrentUserProvider : ICurrentUserProvider
{
    private readonly IHttpContextAccessor _httpContextAccessor;

    public HttpContextCurrentUserProvider(IHttpContextAccessor httpContextAccessor)
        => _httpContextAccessor = httpContextAccessor;

    public Guid? UserId => GetUserId(_httpContextAccessor.HttpContext?.User);

    public bool IsAuthenticated => _httpContextAccessor.HttpContext?.User.Identity?.IsAuthenticated == true;

    private static Guid? GetUserId(ClaimsPrincipal? principal)
    {
        var idClaim = principal?.FindFirst(ClaimTypes.NameIdentifier);
        return idClaim is not null && Guid.TryParse(idClaim.Value, out var id) ? id : null;
    }
}