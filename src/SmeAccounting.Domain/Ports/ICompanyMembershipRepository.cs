using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ICompanyMembershipRepository
{
    Task AddAsync(CompanyMembership membership);
}
