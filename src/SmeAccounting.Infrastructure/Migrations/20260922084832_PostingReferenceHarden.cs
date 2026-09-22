using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class PostingReferenceHarden : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_posting_references_source_type_source_id",
                table: "posting_references");

            migrationBuilder.AddColumn<long>(
                name: "company_id",
                table: "posting_references",
                type: "bigint",
                nullable: false,
                defaultValue: 0L);

            migrationBuilder.CreateIndex(
                name: "IX_posting_references_company_id_source_type_source_id",
                table: "posting_references",
                columns: new[] { "company_id", "source_type", "source_id" },
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_posting_references_companies_company_id",
                table: "posting_references",
                column: "company_id",
                principalTable: "companies",
                principalColumn: "id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_posting_references_journal_entries_journal_entry_id",
                table: "posting_references",
                column: "journal_entry_id",
                principalTable: "journal_entries",
                principalColumn: "id",
                onDelete: ReferentialAction.Restrict);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_posting_references_companies_company_id",
                table: "posting_references");

            migrationBuilder.DropForeignKey(
                name: "FK_posting_references_journal_entries_journal_entry_id",
                table: "posting_references");

            migrationBuilder.DropIndex(
                name: "IX_posting_references_company_id_source_type_source_id",
                table: "posting_references");

            migrationBuilder.DropColumn(
                name: "company_id",
                table: "posting_references");

            migrationBuilder.CreateIndex(
                name: "IX_posting_references_source_type_source_id",
                table: "posting_references",
                columns: new[] { "source_type", "source_id" });
        }
    }
}
