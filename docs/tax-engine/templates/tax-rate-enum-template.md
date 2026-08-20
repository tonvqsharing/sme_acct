# Template — Tax Rate Enum (TaxRate)

Used for: Invoice items, CompanyConfig vat_rates, API validation.

| Value | Meaning | Legal basis | Applicable objects |
|---|---|---|---|
| **VAT_0** | 0% | Xuất khẩu, dịch vụ quốc tế | Hàng xuất khẩu, dịch vụ quốc tế |
| **VAT_5** | 5% | Nước dùng bắt buộc (nước sạch, thuốc, sách, phân, pesticide) | Hàng hóa cần bắt buộc, dịch vụ y tế, giáo dục |
| **VAT_10** | 10% | Chuẩn mực — hàng hóa dịch vụ thường | Hàng hóa dịch vụ thường, BN&SV |
| **NOT_TAXED** | -1 | Miễn thuế GTGT (Cấp theo Điều 5 Luật GTGT) | Mặt hàng không chịu thuế |

## Usage in InvoiceItem

```python
item = InvoiceItem(
    product_name="Sản phẩm XYZ",
    quantity=2.0,
    unit_price=50000.0,
    vat_rate=TaxRate.VAT_10,  # chọn từ enum này
    discount=0.0,
)
# System auto-calculates:
#   line_total  = round(2.0 × 50000.0 - 0.0, 2) = 100000.0
#   vat_amount  = round(100000.0 × 10 / 100, 2) = 10000.0
#   total_amount = round(100000.0 + 10000.0, 2) = 110000.0
```

## Usage in CompanyConfig

```python
config.vat_rates = frozenset({0, 5, 10})  # Default; LAW-type, immutable without migration
```

## Validation rule

```python
def validate_vat_rate(rate: int) -> None:
    if rate not in {0, 5, 10}:
        raise InvalidRegimeError(
            f"Thuế GTGT {rate} không hợp lệ. Các mức được phép: {{0, 5, 10}}"
        )
```