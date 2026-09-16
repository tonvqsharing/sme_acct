using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AccountingFoundation : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<long>(
                name: "cost_center_id",
                table: "journal_entry_lines",
                type: "bigint",
                nullable: true);

            migrationBuilder.AddColumn<long>(
                name: "department_id",
                table: "journal_entry_lines",
                type: "bigint",
                nullable: true);

            migrationBuilder.AddColumn<long>(
                name: "project_id",
                table: "journal_entry_lines",
                type: "bigint",
                nullable: true);

            migrationBuilder.AddColumn<long>(
                name: "company_id",
                table: "fiscal_years",
                type: "bigint",
                nullable: false,
                defaultValue: 0L);

            migrationBuilder.AddColumn<string>(
                name: "description",
                table: "fiscal_years",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<DateOnly>(
                name: "end_date",
                table: "fiscal_years",
                type: "date",
                nullable: false,
                defaultValue: new DateOnly(1, 1, 1));

            migrationBuilder.AddColumn<DateOnly>(
                name: "start_date",
                table: "fiscal_years",
                type: "date",
                nullable: false,
                defaultValue: new DateOnly(1, 1, 1));

            migrationBuilder.AddColumn<DateOnly>(
                name: "end_date",
                table: "fiscal_periods",
                type: "date",
                nullable: false,
                defaultValue: new DateOnly(1, 1, 1));

            migrationBuilder.AddColumn<string>(
                name: "period_type",
                table: "fiscal_periods",
                type: "text",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<DateOnly>(
                name: "start_date",
                table: "fiscal_periods",
                type: "date",
                nullable: false,
                defaultValue: new DateOnly(1, 1, 1));

            migrationBuilder.AddColumn<long>(
                name: "company_id",
                table: "accounts",
                type: "bigint",
                nullable: false,
                defaultValue: 0L);

            migrationBuilder.AddColumn<string>(
                name: "description",
                table: "accounts",
                type: "character varying(500)",
                maxLength: 500,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "normal_balance",
                table: "accounts",
                type: "text",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<long>(
                name: "company_id",
                table: "account_groups",
                type: "bigint",
                nullable: false,
                defaultValue: 0L);

            migrationBuilder.AddColumn<int>(
                name: "display_order",
                table: "account_groups",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.CreateTable(
                name: "companies",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    tax_code = table.Column<string>(type: "character varying(13)", maxLength: 13, nullable: false),
                    address = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    phone = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    email = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    fiscal_year_start_month = table.Column<int>(type: "integer", nullable: false),
                    fiscal_year_start_day = table.Column<int>(type: "integer", nullable: false),
                    functional_currency_code = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_companies", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "currencies",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    code = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    name = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    symbol = table.Column<string>(type: "character varying(10)", maxLength: 10, nullable: false),
                    decimal_places = table.Column<int>(type: "integer", nullable: false),
                    is_default = table.Column<bool>(type: "boolean", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_currencies", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "cost_centers",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_cost_centers", x => x.id);
                    table.ForeignKey(
                        name: "FK_cost_centers_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "departments",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_departments", x => x.id);
                    table.ForeignKey(
                        name: "FK_departments_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "exchange_rates",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    from_currency_code = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    to_currency_code = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    rate = table.Column<decimal>(type: "numeric(10,6)", nullable: false),
                    rate_type = table.Column<string>(type: "text", nullable: false),
                    effective_date = table.Column<DateOnly>(type: "date", nullable: false),
                    source = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_exchange_rates", x => x.id);
                    table.ForeignKey(
                        name: "FK_exchange_rates_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "projects",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    start_date = table.Column<DateOnly>(type: "date", nullable: true),
                    end_date = table.Column<DateOnly>(type: "date", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_projects", x => x.id);
                    table.ForeignKey(
                        name: "FK_projects_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_journal_entry_lines_cost_center_id",
                table: "journal_entry_lines",
                column: "cost_center_id");

            migrationBuilder.CreateIndex(
                name: "IX_journal_entry_lines_department_id",
                table: "journal_entry_lines",
                column: "department_id");

            migrationBuilder.CreateIndex(
                name: "IX_journal_entry_lines_project_id",
                table: "journal_entry_lines",
                column: "project_id");

            migrationBuilder.CreateIndex(
                name: "IX_fiscal_years_company_id",
                table: "fiscal_years",
                column: "company_id");

            migrationBuilder.CreateIndex(
                name: "IX_accounts_company_id",
                table: "accounts",
                column: "company_id");

            migrationBuilder.CreateIndex(
                name: "IX_account_groups_company_id",
                table: "account_groups",
                column: "company_id");

            migrationBuilder.CreateIndex(
                name: "IX_companies_tax_code",
                table: "companies",
                column: "tax_code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_cost_centers_company_id_code",
                table: "cost_centers",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_currencies_code",
                table: "currencies",
                column: "code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_departments_company_id_code",
                table: "departments",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_exchange_rates_company_id_from_currency_code_to_currency_co~",
                table: "exchange_rates",
                columns: new[] { "company_id", "from_currency_code", "to_currency_code", "rate_type", "effective_date" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_projects_company_id_code",
                table: "projects",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_account_groups_companies_company_id",
                table: "account_groups",
                column: "company_id",
                principalTable: "companies",
                principalColumn: "id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_accounts_companies_company_id",
                table: "accounts",
                column: "company_id",
                principalTable: "companies",
                principalColumn: "id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_fiscal_years_companies_company_id",
                table: "fiscal_years",
                column: "company_id",
                principalTable: "companies",
                principalColumn: "id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_journal_entry_lines_cost_centers_cost_center_id",
                table: "journal_entry_lines",
                column: "cost_center_id",
                principalTable: "cost_centers",
                principalColumn: "id",
                onDelete: ReferentialAction.SetNull);

            migrationBuilder.AddForeignKey(
                name: "FK_journal_entry_lines_departments_department_id",
                table: "journal_entry_lines",
                column: "department_id",
                principalTable: "departments",
                principalColumn: "id",
                onDelete: ReferentialAction.SetNull);

            migrationBuilder.AddForeignKey(
                name: "FK_journal_entry_lines_projects_project_id",
                table: "journal_entry_lines",
                column: "project_id",
                principalTable: "projects",
                principalColumn: "id",
                onDelete: ReferentialAction.SetNull);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_account_groups_companies_company_id",
                table: "account_groups");

            migrationBuilder.DropForeignKey(
                name: "FK_accounts_companies_company_id",
                table: "accounts");

            migrationBuilder.DropForeignKey(
                name: "FK_fiscal_years_companies_company_id",
                table: "fiscal_years");

            migrationBuilder.DropForeignKey(
                name: "FK_journal_entry_lines_cost_centers_cost_center_id",
                table: "journal_entry_lines");

            migrationBuilder.DropForeignKey(
                name: "FK_journal_entry_lines_departments_department_id",
                table: "journal_entry_lines");

            migrationBuilder.DropForeignKey(
                name: "FK_journal_entry_lines_projects_project_id",
                table: "journal_entry_lines");

            migrationBuilder.DropTable(
                name: "cost_centers");

            migrationBuilder.DropTable(
                name: "currencies");

            migrationBuilder.DropTable(
                name: "departments");

            migrationBuilder.DropTable(
                name: "exchange_rates");

            migrationBuilder.DropTable(
                name: "projects");

            migrationBuilder.DropTable(
                name: "companies");

            migrationBuilder.DropIndex(
                name: "IX_journal_entry_lines_cost_center_id",
                table: "journal_entry_lines");

            migrationBuilder.DropIndex(
                name: "IX_journal_entry_lines_department_id",
                table: "journal_entry_lines");

            migrationBuilder.DropIndex(
                name: "IX_journal_entry_lines_project_id",
                table: "journal_entry_lines");

            migrationBuilder.DropIndex(
                name: "IX_fiscal_years_company_id",
                table: "fiscal_years");

            migrationBuilder.DropIndex(
                name: "IX_accounts_company_id",
                table: "accounts");

            migrationBuilder.DropIndex(
                name: "IX_account_groups_company_id",
                table: "account_groups");

            migrationBuilder.DropColumn(
                name: "cost_center_id",
                table: "journal_entry_lines");

            migrationBuilder.DropColumn(
                name: "department_id",
                table: "journal_entry_lines");

            migrationBuilder.DropColumn(
                name: "project_id",
                table: "journal_entry_lines");

            migrationBuilder.DropColumn(
                name: "company_id",
                table: "fiscal_years");

            migrationBuilder.DropColumn(
                name: "description",
                table: "fiscal_years");

            migrationBuilder.DropColumn(
                name: "end_date",
                table: "fiscal_years");

            migrationBuilder.DropColumn(
                name: "start_date",
                table: "fiscal_years");

            migrationBuilder.DropColumn(
                name: "end_date",
                table: "fiscal_periods");

            migrationBuilder.DropColumn(
                name: "period_type",
                table: "fiscal_periods");

            migrationBuilder.DropColumn(
                name: "start_date",
                table: "fiscal_periods");

            migrationBuilder.DropColumn(
                name: "company_id",
                table: "accounts");

            migrationBuilder.DropColumn(
                name: "description",
                table: "accounts");

            migrationBuilder.DropColumn(
                name: "normal_balance",
                table: "accounts");

            migrationBuilder.DropColumn(
                name: "company_id",
                table: "account_groups");

            migrationBuilder.DropColumn(
                name: "display_order",
                table: "account_groups");
        }
    }
}
