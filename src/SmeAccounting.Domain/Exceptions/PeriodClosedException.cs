namespace SmeAccounting.Domain.Exceptions;

public class PeriodClosedException : DomainException
{
    public PeriodClosedException(long periodId)
        : base($"Period {periodId} is closed and cannot accept new postings.") { }
}
