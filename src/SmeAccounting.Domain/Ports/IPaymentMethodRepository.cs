using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IPaymentMethodRepository
{
    Task<PaymentMethod?> GetByIdAsync(long id);
    Task<PaymentMethod?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<PaymentMethod>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(PaymentMethod paymentMethod);
}
