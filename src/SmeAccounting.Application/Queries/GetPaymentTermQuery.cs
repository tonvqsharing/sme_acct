using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetPaymentTermQuery(long PaymentTermId) : IRequest<PaymentTermDto?>;
