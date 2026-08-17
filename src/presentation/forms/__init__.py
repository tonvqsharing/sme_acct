"""Forms stubs."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired


class PartnerForm(FlaskForm):
    code = StringField("Mã", validators=[DataRequired()])
    name = StringField("Tên", validators=[DataRequired()])
    entity_type = SelectField(
        "Loại", choices=[("customer", "Khách hàng"), ("supplier", "Nhà cung cấp")]
    )
    tax_id = StringField("Mã số thuế")
    address = TextAreaField("Địa chỉ")
    phone = StringField("Điện thoại")
    email = StringField("Email")
    tax_agency = TextAreaField("Đơn vị thuế")


class InvoiceItemForm(FlaskForm):
    product_name = StringField("Tên hàng", validators=[DataRequired()])
    quantity = DecimalField("Số lượng", default=1)
    unit_price = DecimalField("Đơn giá")
    unit = StringField("ĐVT", default="Cái")
    vat_rate = SelectField("Thuế suất", choices=[(0, "0%"), (5, "5%"), (10, "10%")], default=10)
    discount = DecimalField("Chiết khấu", default=0)
