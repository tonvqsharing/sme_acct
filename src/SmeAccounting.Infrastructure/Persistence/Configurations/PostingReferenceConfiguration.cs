using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class PostingReferenceConfiguration : IEntityTypeConfiguration<PostingReference>
{
    public void Configure(EntityTypeBuilder<PostingReference> builder)
    {
        builder.ToTable("posting_references");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.JournalEntryId)
            .HasColumnName("journal_entry_id");

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.SourceType)
            .HasColumnName("source_type")
            .IsRequired()
            .HasMaxLength(100);

        builder.Property(e => e.SourceId)
            .HasColumnName("source_id");

        builder.HasIndex(e => e.JournalEntryId);
        builder.HasIndex(e => new { e.CompanyId, e.SourceType, e.SourceId })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<JournalEntry>()
            .WithMany()
            .HasForeignKey(e => e.JournalEntryId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
