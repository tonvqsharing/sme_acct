using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class JournalEntryLineConfiguration : IEntityTypeConfiguration<JournalEntryLine>
{
    public void Configure(EntityTypeBuilder<JournalEntryLine> builder)
    {
        builder.ToTable("journal_entry_lines");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.EntryId)
            .HasColumnName("entry_id");

        builder.Property(e => e.AccountId)
            .HasColumnName("account_id");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.OwnsOne(e => e.Debit, moneyBuilder =>
        {
            moneyBuilder.Property(m => m.Amount)
                .HasColumnName("debit_amount");

            moneyBuilder.Property(m => m.Currency)
                .HasColumnName("debit_currency")
                .HasMaxLength(3);
        });

        builder.OwnsOne(e => e.Credit, moneyBuilder =>
        {
            moneyBuilder.Property(m => m.Amount)
                .HasColumnName("credit_amount");

            moneyBuilder.Property(m => m.Currency)
                .HasColumnName("credit_currency")
                .HasMaxLength(3);
        });

        builder.HasIndex(e => e.EntryId);
        builder.HasIndex(e => e.AccountId);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
