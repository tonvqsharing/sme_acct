namespace SmeAccounting.SharedKernel;

public interface ICurrentUserProvider
{
    Guid? UserId { get; }

    bool IsAuthenticated { get; }
}