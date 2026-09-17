using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IPaymentTermRepository
{
    Task<PaymentTerm?> GetByIdAsync(long id);
    Task<PaymentTerm?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<PaymentTerm>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(PaymentTerm paymentTerm);
}
