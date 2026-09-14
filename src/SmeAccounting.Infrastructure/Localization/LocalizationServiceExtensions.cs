using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Localization;
using Microsoft.Extensions.DependencyInjection;
using System.Globalization;

namespace SmeAccounting.Infrastructure.Localization;

public static class LocalizationServiceExtensions
{
    public static IServiceCollection AddLocalizationInfrastructure(this IServiceCollection services)
    {
        services.AddLocalization(options => options.ResourcesPath = "Resources");

        services.Configure<RequestLocalizationOptions>(options =>
        {
            CultureInfo[] supportedCultures;
            RequestCulture defaultCulture;

            try
            {
                supportedCultures =
                [
                    new CultureInfo("vi-VN"),
                    new CultureInfo("en-US")
                ];
                defaultCulture = new RequestCulture("vi-VN");
            }
            catch (CultureNotFoundException)
            {
                // Globalization-invariant mode (e.g. in test environments)
                supportedCultures = [CultureInfo.InvariantCulture];
                defaultCulture = new RequestCulture(CultureInfo.InvariantCulture);
            }

            options.DefaultRequestCulture = defaultCulture;
            options.SupportedCultures = supportedCultures;
            options.SupportedUICultures = supportedCultures;
        });

        return services;
    }
}
