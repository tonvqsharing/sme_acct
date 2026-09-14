using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.Hosting;

namespace SmeAccounting.Web.Tests;

public class TestWebApplicationFactory : WebApplicationFactory<Program>
{
    protected override IHost CreateHost(IHostBuilder builder)
    {
        builder.UseEnvironment("Testing");
        builder.ConfigureServices(services =>
        {
            // Remove DB-dependent health checks (NpgsqlDataSource not available in test env)
            var healthCheckDescriptors = services
                .Where(d => d.ServiceType == typeof(IHealthCheck))
                .ToList();
            foreach (var d in healthCheckDescriptors)
                services.Remove(d);

            services.Configure<HealthCheckServiceOptions>(options =>
            {
                options.Registrations.Clear();
            });
        });
        return base.CreateHost(builder);
    }
}
