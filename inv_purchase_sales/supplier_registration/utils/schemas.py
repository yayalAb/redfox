from pydantic import (
    BaseModel, Field, field_validator,
    model_validator, EmailStr, conbytes, ConfigDict, Base64Str,
    Base64Bytes, StringConstraints
)
from typing import List, Optional, Annotated
from collections import defaultdict
from datetime import date, datetime
import re
import base64

DOC_MAX_SIZE = 1 * 1024 * 1024 # 1 MB
DOC_MIMETYPES = ['application/pdf', 'image/jpeg', 'image/png']
TRADE_LIC_TYPE = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9]{8,20}$")]
TINType = Annotated[str, StringConstraints(pattern=r"^\d{10}$")]

class ContactSchema(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str

class ContactOutSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    name: str
    email: EmailStr
    phone: str
    street: str = Field(alias='address')
    company_type: str = 'person'
    type: str = 'contact'

    def model_dump(self, **kwargs):
        data = super().model_dump()
        data['function'] = kwargs.get('function')
        return data

class ClientContactSchema(BaseModel):
    name: str = None
    email: EmailStr = None
    phone: str = None
    address: str = None
    
    @model_validator(mode='before')
    @classmethod
    def check_name_required(cls, values):
        name = values.get('name')
        email = values.get('email')
        phone = values.get('phone')
        address = values.get('address')

        if (email or phone or address) and not name:
            raise ValueError("If email, phone, or address is provided, name must also be provided.")
        return values

class ClientContactOutSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    name: str
    email: EmailStr | bool
    phone: str | bool
    street: str | bool = Field(alias='address')

class SupplierRegistrationSchema(BaseModel):
    name: str = Field(alias='company_name')
    company_category_type: str
    email: EmailStr
    image_1920: Base64Bytes
    street: str
    street2: str = None
    product_category_id : int
    trade_license_number: Optional[TRADE_LIC_TYPE] = None
    vat: Optional[TINType] = None
    commencement_date: Optional[date] = None
    primary_contact_id: ContactSchema
    finance_contact_id: Optional[ContactSchema] = None
    authorized_contact_id: Optional[ContactSchema] = None
    expiry_date: Optional[date] = None
    # Bank info
    bank_name: str = None
    swift_code: str = None
    iban: str = None
    branch_address: str = None
    acc_holder_name: str = None
    acc_number: str = None
    # certification
    certification_name: str = None
    certificate_number: str = None
    certifying_body: str = None
    certification_award_date: Optional[date] = None
    certification_expiry_date: Optional[date] = None
    # client references
    client_ref_ids: List[ClientContactSchema] = []
    # docs
    trade_license_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    certificate_of_incorporation_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    certificate_of_good_standing_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    establishment_card_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    vat_tax_certificate_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    memorandum_of_association_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    identification_of_authorised_person_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    bank_letter_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    past_2_years_financial_statement_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    other_certification_doc: conbytes(max_length=DOC_MAX_SIZE) = None # type: ignore
    company_stamp: conbytes(max_length=DOC_MAX_SIZE) # type: ignore
    #signatory
    signatory_name: str
    authorized_signatory_name: str
    supplier_type: str

    @model_validator(mode='before')
    @classmethod
    def preprocess_data(cls, values):
        groups_types = {'contact', 'client'}
        group_collections = defaultdict(dict)
        for key in values.keys():
            match = re.match(r"([a-zA-Z]+)_(\d+)_(.+)", key)
            if match:
                group, index, field = match.groups()
                if group in groups_types:
                    group_collections[f"{group}_{index}"][field] = values[key]
        grouped_data = dict(group_collections)
        contact_mapping = {
            'contact_1': 'primary_contact_id',
            'contact_2': 'finance_contact_id',
            'contact_3': 'authorized_contact_id'
        }
        for key in contact_mapping.keys():
            if key in grouped_data:
                values[contact_mapping[key]] = grouped_data[key]
        client_ref_ids = []
        for key in grouped_data.keys():
            if 'client' in key:
                client_ref_ids.append(grouped_data[key])
        values['client_ref_ids'] = client_ref_ids
        # Binary fields
        binary_file_fields = [
            'image_1920',
            'company_stamp',
            'trade_license_doc',
            'certificate_of_incorporation_doc',
            'certificate_of_good_standing_doc',
            'establishment_card_doc',
            'vat_tax_certificate_doc',
            'memorandum_of_association_doc',
            'identification_of_authorised_person_doc',
            'bank_letter_doc',
            'past_2_years_financial_statement_doc',
            'other_certification_doc',
        ]
        for field in binary_file_fields:
            if field in values:
                file_value = values[field]
                filename = file_value.filename
                mimetype = file_value.mimetype
                if mimetype not in DOC_MIMETYPES:
                    raise ValueError(f"Invalid file format for {filename}. Please upload a valid PDF or image file.")
                values[field] = cls.transform_binary_fields(file_value)
        return values

    @classmethod
    def transform_binary_fields(cls, value):
        if value and hasattr(value, 'read'):
            return base64.b64encode(value.read())
        return value

    @field_validator('commencement_date')
    @classmethod
    def validate_commencement_date(cls, value):
        if value and value >= date.today():
            raise ValueError("Commencement date must be in the past.")
        return value

    @field_validator('expiry_date')
    @classmethod
    def validate_expiry_date(cls, value):
        if value and value <= date.today():
            raise ValueError("Expiry date must be in the future.")
        return value

    @field_validator('certification_award_date')
    @classmethod
    def validate_certification_award_date(cls, value):
        if value and value >= date.today():
            raise ValueError("Certification Award date must be in the past.")
        return value

    @field_validator('certification_expiry_date')
    @classmethod
    def validate_certification_expiry_date(cls, value):
        if value and value <= date.today():
            raise ValueError("Certification Expiry date must be in the future.")
        return value

class BankSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    name: str | bool
    swift_code: str | bool
    iban: str | bool 

class BankAccountSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    branch_address: str | bool
    acc_holder_name: str | bool
    acc_number: str | bool

    def model_dump(self, **kwargs):
        data = super().model_dump()
        bank_id = kwargs.get('bank_id')
        if bank_id:
            data['bank_id'] = bank_id
        return data

class UserSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    login: EmailStr = Field(alias='email')
    password: str = Field(alias='email')

    def model_dump(self, **kwargs):
        data = super().model_dump()
        data['partner_id'] = kwargs.get('partner_id')
        data['company_id'] = kwargs.get('company_id')
        data['groups_id'] = kwargs.get('groups_id')
        return data

class CompanySchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    name: str
    company_category_type: str
    product_category_id: int
    email: EmailStr
    street: str
    phone: Optional[str] | None = None
    street2: Optional[str] | bool
    image_1920: Optional[Base64Bytes] | bool
    company_stamp: Optional[Base64Bytes] | bool
    trade_license_number: Optional[str] | bool
    vat: Optional[str] | bool
    commencement_date: Optional[date] | bool
    expiry_date: Optional[date] | bool
    certification_name: Optional[str] | bool
    certificate_number: Optional[str] | bool
    certifying_body: Optional[str] | bool
    certification_award_date: Optional[date] | bool
    certification_expiry_date: Optional[date] | bool
    trade_license_doc: Optional[bytes] | bool
    certificate_of_incorporation_doc: Optional[bytes] | bool
    certificate_of_good_standing_doc: Optional[bytes] | bool
    establishment_card_doc: Optional[bytes] | bool
    vat_tax_certificate_doc: Optional[bytes] | bool
    memorandum_of_association_doc: Optional[bytes] | bool
    identification_of_authorised_person_doc: Optional[bytes] | bool
    bank_letter_doc: Optional[bytes] | bool
    past_2_years_financial_statement_doc: Optional[bytes] | bool
    other_certification_doc: Optional[bytes] | bool
    signatory_name: str
    authorized_signatory_name: str
    date_registration: datetime
    supplier_rank: int = 1
    company_type: str = 'company'
    supplier_type: str

    @model_validator(mode='before')
    @classmethod
    def preprocess_data(cls, values):
        if not isinstance(values, dict):
            data = {}
            for field in cls.model_fields:
                if hasattr(values, field):
                    data[field] = getattr(values, field)
            if hasattr(values, 'primary_contact_id'):
                data['primary_contact_id'] = getattr(values, 'primary_contact_id')
            data['date_registration'] = values.create_date
            product_category = getattr(values, 'product_category_id')
            data['product_category_id'] = getattr(product_category, 'id') or False
            values = data

        if 'primary_contact_id' in values:
            primary_contact = values['primary_contact_id']
            if hasattr(primary_contact, 'phone'):
                values['phone'] = primary_contact.phone
        return values

class EditProfileSchema(BaseModel):
    street: str = None
    product_category_id: int = None
    trade_license_number: Optional[TRADE_LIC_TYPE] = None
    vat: Optional[TINType] = None
    commencement_date: Optional[date] = None
    expiry_date: Optional[date] = None
    phone: Optional[str] = None

    # Certification
    certification_name: Optional[str] = None
    certificate_number: Optional[str] = None
    certifying_body: Optional[str] = None
    certification_award_date: Optional[date] = None
    certification_expiry_date: Optional[date] = None

    # Documents
    trade_license_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    certificate_of_incorporation_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    certificate_of_good_standing_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    establishment_card_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    vat_tax_certificate_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    memorandum_of_association_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    identification_of_authorised_person_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    bank_letter_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    past_2_years_financial_statement_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    other_certification_doc: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None
    company_stamp: Optional[conbytes(max_length=DOC_MAX_SIZE)] = None

    # Signatory
    signatory_name: Optional[str] = None
    authorized_signatory_name: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def preprocess_data(cls, values):
        binary_file_fields = [
            'company_stamp',
            'trade_license_doc',
            'certificate_of_incorporation_doc',
            'certificate_of_good_standing_doc',
            'establishment_card_doc',
            'vat_tax_certificate_doc',
            'memorandum_of_association_doc',
            'identification_of_authorised_person_doc',
            'bank_letter_doc',
            'past_2_years_financial_statement_doc',
            'other_certification_doc',
        ]
        for field in binary_file_fields:
            if field in values:
                file_value = values[field]
                if not file_value:
                    values.pop(field)
                    continue
                filename = file_value.filename
                mimetype = file_value.mimetype
                if mimetype not in DOC_MIMETYPES:
                    raise ValueError(f"Invalid file format for {filename} for field: {field}. Please upload a valid PDF or image file.")
                values[field] = cls.transform_binary_fields(file_value)
        return values

    @classmethod
    def transform_binary_fields(cls, value):
        if value and hasattr(value, 'read'):
            return base64.b64encode(value.read())
        return value

    @field_validator('commencement_date')
    @classmethod
    def validate_commencement_date(cls, value):
        if value and value >= date.today():
            raise ValueError("Commencement date must be in the past.")
        return value

    @field_validator('expiry_date')
    @classmethod
    def validate_expiry_date(cls, value):
        if value and value <= date.today():
            raise ValueError("Expiry date must be in the future.")
        return value

    @field_validator('certification_award_date')
    @classmethod
    def validate_certification_award_date(cls, value):
        if value and value >= date.today():
            raise ValueError("Certification Award date must be in the past.")
        return value

    @field_validator('certification_expiry_date')
    @classmethod
    def validate_certification_expiry_date(cls, value):
        if value and value <= date.today():
            raise ValueError("Certification Expiry date must be in the future.")
        return value