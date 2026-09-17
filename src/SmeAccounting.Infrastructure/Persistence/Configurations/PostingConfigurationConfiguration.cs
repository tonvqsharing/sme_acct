using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class PostingConfigurationConfiguration : IEntityTypeConfiguration<PostingConfiguration>
{
    public void Configure(EntityTypeBuilder<PostingConfiguration> builder)
    {
        builder.ToTable("posting_configurations");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.VoucherTypeId)
            .HasColumnName("voucher_type_id");

        builder.Property(e => e.DebitAccountId)
            .HasColumnName("debit_account_id");

        builder.Property(e => e.CreditAccountId)
            .HasColumnName("credit_account_id");

        builder.Property(e => e.TransactionReasonId)
            .HasColumnName("transaction_reason_id");

        builder.Property(e => e.DisplayOrder)
            .HasColumnName("display_order");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.VoucherTypeId, e.TransactionReasonId });

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<VoucherType>()
            .WithMany()
            .HasForeignKey(e => e.VoucherTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.DebitAccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.CreditAccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TransactionReason>()
            .WithMany()
            .HasForeignKey(e => e.TransactionReasonId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
