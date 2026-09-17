using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class DocumentNumberingSeriesConfiguration : IEntityTypeConfiguration<DocumentNumberingSeries>
{
    public void Configure(EntityTypeBuilder<DocumentNumberingSeries> builder)
    {
        builder.ToTable("document_numbering_series");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.VoucherTypeId)
            .HasColumnName("voucher_type_id");

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.Prefix)
            .HasColumnName("prefix")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.NextNumber)
            .HasColumnName("next_number");

        builder.Property(e => e.PaddingLength)
            .HasColumnName("padding_length");

        builder.Property(e => e.IsDefault)
            .HasColumnName("is_default");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.VoucherTypeId, e.CompanyId, e.Prefix })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<VoucherType>()
            .WithMany()
            .HasForeignKey(e => e.VoucherTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
