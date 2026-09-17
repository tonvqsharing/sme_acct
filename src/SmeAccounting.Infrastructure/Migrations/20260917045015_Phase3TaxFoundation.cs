using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class Phase3TaxFoundation : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "tax_authorities",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    authority_level = table.Column<string>(type: "text", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    address = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    phone = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_authorities", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_authorities_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tax_types",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    tax_category = table.Column<string>(type: "text", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_types", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_types_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tax_exemption_reasons",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_type_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    legal_basis = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_exemption_reasons", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_exemption_reasons_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_exemption_reasons_tax_types_tax_type_id",
                        column: x => x.tax_type_id,
                        principalTable: "tax_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tax_periods",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    fiscal_period_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_type_id = table.Column<long>(type: "bigint", nullable: false),
                    filing_deadline = table.Column<DateOnly>(type: "date", nullable: false),
                    filing_frequency = table.Column<string>(type: "text", nullable: false),
                    status = table.Column<string>(type: "text", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_periods", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_periods_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_periods_fiscal_periods_fiscal_period_id",
                        column: x => x.fiscal_period_id,
                        principalTable: "fiscal_periods",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_periods_tax_types_tax_type_id",
                        column: x => x.tax_type_id,
                        principalTable: "tax_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tax_rates",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_type_id = table.Column<long>(type: "bigint", nullable: false),
                    rate_value = table.Column<decimal>(type: "numeric(5,2)", nullable: false),
                    rate_name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    effective_from = table.Column<DateOnly>(type: "date", nullable: false),
                    effective_to = table.Column<DateOnly>(type: "date", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_rates", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_rates_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_rates_tax_types_tax_type_id",
                        column: x => x.tax_type_id,
                        principalTable: "tax_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tax_treatments",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    tax_type_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_treatment_type = table.Column<string>(type: "text", nullable: false),
                    input_credit_allowed = table.Column<bool>(type: "boolean", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_treatments", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_treatments_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_treatments_tax_types_tax_type_id",
                        column: x => x.tax_type_id,
                        principalTable: "tax_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tax_accounting_mappings",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_type_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_treatment_id = table.Column<long>(type: "bigint", nullable: false),
                    account_id = table.Column<long>(type: "bigint", nullable: false),
                    mapping_type = table.Column<string>(type: "text", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_accounting_mappings", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_accounting_mappings_accounts_account_id",
                        column: x => x.account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_accounting_mappings_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_accounting_mappings_tax_treatments_tax_treatment_id",
                        column: x => x.tax_treatment_id,
                        principalTable: "tax_treatments",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_accounting_mappings_tax_types_tax_type_id",
                        column: x => x.tax_type_id,
                        principalTable: "tax_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tax_rules",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_type_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_rate_id = table.Column<long>(type: "bigint", nullable: true),
                    tax_treatment_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    conditions = table.Column<string>(type: "text", nullable: true),
                    legal_reference = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    effective_from = table.Column<DateOnly>(type: "date", nullable: false),
                    effective_to = table.Column<DateOnly>(type: "date", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tax_rules", x => x.id);
                    table.ForeignKey(
                        name: "FK_tax_rules_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_rules_tax_rates_tax_rate_id",
                        column: x => x.tax_rate_id,
                        principalTable: "tax_rates",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_rules_tax_treatments_tax_treatment_id",
                        column: x => x.tax_treatment_id,
                        principalTable: "tax_treatments",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tax_rules_tax_types_tax_type_id",
                        column: x => x.tax_type_id,
                        principalTable: "tax_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_tax_accounting_mappings_account_id",
                table: "tax_accounting_mappings",
                column: "account_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_accounting_mappings_company_id_mapping_type",
                table: "tax_accounting_mappings",
                columns: new[] { "company_id", "mapping_type" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tax_accounting_mappings_tax_treatment_id",
                table: "tax_accounting_mappings",
                column: "tax_treatment_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_accounting_mappings_tax_type_id",
                table: "tax_accounting_mappings",
                column: "tax_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_authorities_company_id_code",
                table: "tax_authorities",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tax_exemption_reasons_company_id_code",
                table: "tax_exemption_reasons",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tax_exemption_reasons_tax_type_id",
                table: "tax_exemption_reasons",
                column: "tax_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_periods_company_id_fiscal_period_id_tax_type_id",
                table: "tax_periods",
                columns: new[] { "company_id", "fiscal_period_id", "tax_type_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tax_periods_fiscal_period_id",
                table: "tax_periods",
                column: "fiscal_period_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_periods_tax_type_id",
                table: "tax_periods",
                column: "tax_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_rates_company_id_tax_type_id_rate_value_effective_from",
                table: "tax_rates",
                columns: new[] { "company_id", "tax_type_id", "rate_value", "effective_from" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tax_rates_tax_type_id",
                table: "tax_rates",
                column: "tax_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_rules_company_id_code",
                table: "tax_rules",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tax_rules_tax_rate_id",
                table: "tax_rules",
                column: "tax_rate_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_rules_tax_treatment_id",
                table: "tax_rules",
                column: "tax_treatment_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_rules_tax_type_id",
                table: "tax_rules",
                column: "tax_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_treatments_company_id_code",
                table: "tax_treatments",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tax_treatments_tax_type_id",
                table: "tax_treatments",
                column: "tax_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_tax_types_company_id_code",
                table: "tax_types",
                columns: new[] { "company_id", "code" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "tax_accounting_mappings");

            migrationBuilder.DropTable(
                name: "tax_authorities");

            migrationBuilder.DropTable(
                name: "tax_exemption_reasons");

            migrationBuilder.DropTable(
                name: "tax_periods");

            migrationBuilder.DropTable(
                name: "tax_rules");

            migrationBuilder.DropTable(
                name: "tax_rates");

            migrationBuilder.DropTable(
                name: "tax_treatments");

            migrationBuilder.DropTable(
                name: "tax_types");
        }
    }
}
