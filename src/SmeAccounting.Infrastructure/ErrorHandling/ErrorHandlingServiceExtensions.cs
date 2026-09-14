using Microsoft.AspNetCore.Builder;

namespace SmeAccounting.Infrastructure.ErrorHandling;

public static class ErrorHandlingServiceExtensions
{
    public static IApplicationBuilder UseGlobalExceptionHandler(this IApplicationBuilder app)
    {
        return app.UseMiddleware<GlobalExceptionMiddleware>();
    }
}
