using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class AccountConfiguration : IEntityTypeConfiguration<Account>
{
    public void Configure(EntityTypeBuilder<Account> builder)
    {
        builder.ToTable("accounts");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.Level)
            .HasColumnName("level");

        builder.Property(e => e.ParentId)
            .HasColumnName("parent_id");

        builder.Property(e => e.AccountType)
            .HasColumnName("account_type")
            .HasConversion<string>();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.AccountGroupId)
            .HasColumnName("account_group_id");

        builder.OwnsOne(e => e.Code, codeBuilder =>
        {
            codeBuilder.Property(c => c.Value)
                .HasColumnName("code")
                .IsRequired()
                .HasMaxLength(20);
        });

        builder.HasOne<Account>()
            .WithMany(a => a.Children)
            .HasForeignKey(e => e.ParentId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => e.ParentId);
        builder.HasIndex(e => e.Code.Value);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
