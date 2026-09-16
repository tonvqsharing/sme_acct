namespace SmeAccounting.Domain.Exceptions;

public class InvalidPostingRuleException : DomainException
{
    public InvalidPostingRuleException(string message) : base(message) { }
}
