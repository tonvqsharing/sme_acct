namespace SmeAccounting.SharedKernel;

public interface ICompanyScoped
{
    Guid CompanyId { get; set; }
}