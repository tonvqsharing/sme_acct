using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class JournalEntryConfiguration : IEntityTypeConfiguration<JournalEntry>
{
    public void Configure(EntityTypeBuilder<JournalEntry> builder)
    {
        builder.ToTable("journal_entries");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.EntryNumber)
            .HasColumnName("entry_number")
            .IsRequired()
            .HasMaxLength(50);

        builder.Property(e => e.Date)
            .HasColumnName("date");

        builder.Property(e => e.PeriodId)
            .HasColumnName("period_id");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.Property(e => e.SourceType)
            .HasColumnName("source_type")
            .HasMaxLength(100);

        builder.Property(e => e.SourceId)
            .HasColumnName("source_id");

        builder.Property(e => e.PostedBy)
            .HasColumnName("posted_by")
            .HasMaxLength(100);

        builder.Property(e => e.PostedAt)
            .HasColumnName("posted_at");

        builder.Property(e => e.IsPosted)
            .HasColumnName("is_posted");

        builder.HasIndex(e => e.PeriodId);
        builder.HasIndex(e => e.EntryNumber);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
