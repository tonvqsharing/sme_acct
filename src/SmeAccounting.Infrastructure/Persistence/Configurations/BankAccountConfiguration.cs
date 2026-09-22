using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class BankAccountConfiguration : IEntityTypeConfiguration<BankAccount>
{
    public void Configure(EntityTypeBuilder<BankAccount> builder)
    {
        builder.ToTable("bank_accounts");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.BankId)
            .HasColumnName("bank_id");

        builder.Property(e => e.BankBranchId)
            .HasColumnName("bank_branch_id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(50);

        builder.Property(e => e.AccountNumber)
            .HasColumnName("account_number")
            .IsRequired()
            .HasMaxLength(50);

        builder.Property(e => e.AccountName)
            .HasColumnName("account_name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.Property(e => e.CurrencyCode)
            .HasColumnName("currency_code")
            .HasMaxLength(3);

        builder.HasIndex(e => new { e.CompanyId, e.BankId, e.BankBranchId, e.Code })
            .IsUnique();

        builder.HasIndex(e => new { e.CompanyId, e.AccountNumber })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Bank>()
            .WithMany()
            .HasForeignKey(e => e.BankId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<BankBranch>()
            .WithMany()
            .HasForeignKey(e => e.BankBranchId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
