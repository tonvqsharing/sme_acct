using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class Phase2AccountingControlConfig : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "voucher_types",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    voucher_category = table.Column<string>(type: "text", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_voucher_types", x => x.id);
                    table.ForeignKey(
                        name: "FK_voucher_types_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "document_numbering_series",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    voucher_type_id = table.Column<long>(type: "bigint", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    prefix = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    next_number = table.Column<int>(type: "integer", nullable: false),
                    padding_length = table.Column<int>(type: "integer", nullable: false),
                    is_default = table.Column<bool>(type: "boolean", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_document_numbering_series", x => x.id);
                    table.ForeignKey(
                        name: "FK_document_numbering_series_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_document_numbering_series_voucher_types_voucher_type_id",
                        column: x => x.voucher_type_id,
                        principalTable: "voucher_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "opening_balance_mappings",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    voucher_type_id = table.Column<long>(type: "bigint", nullable: false),
                    debit_account_id = table.Column<long>(type: "bigint", nullable: false),
                    credit_account_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_opening_balance_mappings", x => x.id);
                    table.ForeignKey(
                        name: "FK_opening_balance_mappings_accounts_credit_account_id",
                        column: x => x.credit_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_opening_balance_mappings_accounts_debit_account_id",
                        column: x => x.debit_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_opening_balance_mappings_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_opening_balance_mappings_voucher_types_voucher_type_id",
                        column: x => x.voucher_type_id,
                        principalTable: "voucher_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "transaction_reasons",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    voucher_type_id = table.Column<long>(type: "bigint", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_transaction_reasons", x => x.id);
                    table.ForeignKey(
                        name: "FK_transaction_reasons_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_transaction_reasons_voucher_types_voucher_type_id",
                        column: x => x.voucher_type_id,
                        principalTable: "voucher_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "posting_configurations",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    voucher_type_id = table.Column<long>(type: "bigint", nullable: false),
                    debit_account_id = table.Column<long>(type: "bigint", nullable: false),
                    credit_account_id = table.Column<long>(type: "bigint", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    transaction_reason_id = table.Column<long>(type: "bigint", nullable: true),
                    display_order = table.Column<int>(type: "integer", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_posting_configurations", x => x.id);
                    table.ForeignKey(
                        name: "FK_posting_configurations_accounts_credit_account_id",
                        column: x => x.credit_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_posting_configurations_accounts_debit_account_id",
                        column: x => x.debit_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_posting_configurations_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_posting_configurations_transaction_reasons_transaction_reas~",
                        column: x => x.transaction_reason_id,
                        principalTable: "transaction_reasons",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_posting_configurations_voucher_types_voucher_type_id",
                        column: x => x.voucher_type_id,
                        principalTable: "voucher_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_document_numbering_series_company_id",
                table: "document_numbering_series",
                column: "company_id");

            migrationBuilder.CreateIndex(
                name: "IX_document_numbering_series_voucher_type_id_company_id_prefix",
                table: "document_numbering_series",
                columns: new[] { "voucher_type_id", "company_id", "prefix" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_mappings_company_id_voucher_type_id_debit_a~",
                table: "opening_balance_mappings",
                columns: new[] { "company_id", "voucher_type_id", "debit_account_id", "credit_account_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_mappings_credit_account_id",
                table: "opening_balance_mappings",
                column: "credit_account_id");

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_mappings_debit_account_id",
                table: "opening_balance_mappings",
                column: "debit_account_id");

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_mappings_voucher_type_id",
                table: "opening_balance_mappings",
                column: "voucher_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_posting_configurations_company_id",
                table: "posting_configurations",
                column: "company_id");

            migrationBuilder.CreateIndex(
                name: "IX_posting_configurations_credit_account_id",
                table: "posting_configurations",
                column: "credit_account_id");

            migrationBuilder.CreateIndex(
                name: "IX_posting_configurations_debit_account_id",
                table: "posting_configurations",
                column: "debit_account_id");

            migrationBuilder.CreateIndex(
                name: "IX_posting_configurations_transaction_reason_id",
                table: "posting_configurations",
                column: "transaction_reason_id");

            migrationBuilder.CreateIndex(
                name: "IX_posting_configurations_voucher_type_id_transaction_reason_id",
                table: "posting_configurations",
                columns: new[] { "voucher_type_id", "transaction_reason_id" });

            migrationBuilder.CreateIndex(
                name: "IX_transaction_reasons_company_id_code",
                table: "transaction_reasons",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_transaction_reasons_voucher_type_id",
                table: "transaction_reasons",
                column: "voucher_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_voucher_types_company_id_code",
                table: "voucher_types",
                columns: new[] { "company_id", "code" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "document_numbering_series");

            migrationBuilder.DropTable(
                name: "opening_balance_mappings");

            migrationBuilder.DropTable(
                name: "posting_configurations");

            migrationBuilder.DropTable(
                name: "transaction_reasons");

            migrationBuilder.DropTable(
                name: "voucher_types");
        }
    }
}
