using System.Net;
using Microsoft.AspNetCore.Mvc.Testing;

namespace SmeAccounting.Web.Tests;

/// <summary>
/// RolesController is cookie-auth protected: anonymous requests redirect
/// to /Accounts/Login (302), they do NOT return 401/403.
/// </summary>
public class RolesEndpointTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public RolesEndpointTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient(new WebApplicationFactoryClientOptions { AllowAutoRedirect = false });
    }

    [Fact]
    public async Task RolesIndex_Anonymous_RedirectsToLogin()
    {
        var response = await _client.GetAsync("/Roles");

        Assert.Equal(HttpStatusCode.Redirect, response.StatusCode);
        Assert.Contains("/Accounts/Login", response.Headers.Location?.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task RolesPermissions_Anonymous_RedirectsToLogin()
    {
        var response = await _client.GetAsync("/Roles/Permissions?roleName=Admin");

        Assert.Equal(HttpStatusCode.Redirect, response.StatusCode);
        Assert.Contains("/Accounts/Login", response.Headers.Location?.ToString(), StringComparison.OrdinalIgnoreCase);
    }
}
