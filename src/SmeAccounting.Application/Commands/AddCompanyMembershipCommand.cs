using MediatR;

namespace SmeAccounting.Application.Commands;

public record AddCompanyMembershipCommand(
    long UserId,
    long CompanyId) : IRequest<AddCompanyMembershipResult>;

public record AddCompanyMembershipResult(long Id);
