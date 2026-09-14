using Microsoft.AspNetCore.Builder;

namespace SmeAccounting.Infrastructure.Security;

public static class SecurityServiceExtensions
{
    public static IApplicationBuilder UseSecurityHeaders(this IApplicationBuilder app)
    {
        return app.UseMiddleware<SecurityHeadersMiddleware>();
    }
}
