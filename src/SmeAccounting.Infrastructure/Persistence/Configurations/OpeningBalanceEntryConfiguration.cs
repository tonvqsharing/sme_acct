using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class OpeningBalanceEntryConfiguration : IEntityTypeConfiguration<OpeningBalanceEntry>
{
    public void Configure(EntityTypeBuilder<OpeningBalanceEntry> builder)
    {
        builder.ToTable("opening_balance_entries");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.OpeningBalancePeriodId)
            .HasColumnName("opening_balance_period_id");

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.AccountId)
            .HasColumnName("account_id");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.OwnsOne(e => e.Debit, debit =>
        {
            debit.Property(m => m.Amount)
                .HasColumnName("debit_amount")
                .HasColumnType("decimal(19,4)");

            debit.Property(m => m.Currency)
                .HasColumnName("debit_currency")
                .HasMaxLength(3);
        });

        builder.OwnsOne(e => e.Credit, credit =>
        {
            credit.Property(m => m.Amount)
                .HasColumnName("credit_amount")
                .HasColumnType("decimal(19,4)");

            credit.Property(m => m.Currency)
                .HasColumnName("credit_currency")
                .HasMaxLength(3);
        });

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.AccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<OpeningBalancePeriod>()
            .WithMany()
            .HasForeignKey(e => e.OpeningBalancePeriodId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => new { e.CompanyId, e.OpeningBalancePeriodId, e.AccountId })
            .IsUnique();

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
