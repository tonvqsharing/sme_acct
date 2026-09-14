using System.Text.Json;
using HealthChecks.NpgSql;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Health;

public static class HealthServiceExtensions
{
    private static readonly JsonSerializerOptions s_jsonOptions = new() { WriteIndented = true };

    public static IServiceCollection AddHealthInfrastructure(this IServiceCollection services)
    {
        services.AddHealthChecks()
            .AddNpgSql(
                name: "postgresql",
                tags: ["ready", "db"])
            .AddDbContextCheck<SmeAccountingDbContext>(
                name: "efcore",
                tags: ["ready", "db"]);

        return services;
    }

    public static IApplicationBuilder UseHealthInfrastructure(this IApplicationBuilder app)
    {
        app.UseEndpoints(endpoints =>
        {
            endpoints.MapHealthChecks("/health/live", new HealthCheckOptions
            {
                Predicate = _ => false,
                ResponseWriter = WriteResponse
            });

            endpoints.MapHealthChecks("/health/ready", new HealthCheckOptions
            {
                Predicate = check => check.Tags.Contains("ready"),
                ResponseWriter = WriteResponse
            });
        });

        return app;
    }

    private static Task WriteResponse(HttpContext context, HealthReport report)
    {
        context.Response.ContentType = "application/json";

        var result = new
        {
            status = report.Status.ToString(),
            checks = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString(),
                duration = e.Value.Duration.TotalMilliseconds,
                description = e.Value.Description,
                exception = e.Value.Exception?.Message,
                tags = e.Value.Tags
            }),
            totalDuration = report.TotalDuration.TotalMilliseconds
        };

        return context.Response.WriteAsync(
            JsonSerializer.Serialize(result, s_jsonOptions));
    }
}
