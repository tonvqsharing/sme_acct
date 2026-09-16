using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IProjectRepository
{
    Task<Project?> GetByIdAsync(long id);
    Task<Project?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Project>> GetAllAsync();
    Task AddAsync(Project project);
}
