namespace SmeAccounting.Domain.Exceptions;

public class AccountNotLeafException : DomainException
{
    public AccountNotLeafException(long accountId)
        : base($"Account {accountId} has child accounts and cannot accept postings.") { }
}
