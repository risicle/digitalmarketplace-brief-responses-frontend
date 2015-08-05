from flask import render_template, request, redirect, url_for, abort, session
from flask_login import login_required, current_user

from dmutils.apiclient import APIError
from dmutils import flask_featureflags

from ...main import main
from ... import data_api_client
from ..forms.suppliers import EditSupplierForm, EditContactInformationForm, \
    DunsNumberForm, CompaniesHouseNumberForm, CompanyContactDetailsForm, CompanyNameForm
from .users import get_current_suppliers_users


@main.route('')
@login_required
@flask_featureflags.is_active_feature('SUPPLIER_DASHBOARD',
                                      redirect='.list_services')
def dashboard():
    template_data = main.config['BASE_TEMPLATE_DATA']

    try:
        supplier = data_api_client.get_supplier(
            current_user.supplier_id
        )['suppliers']
        supplier['contact'] = supplier['contactInformation'][0]
    except APIError as e:
        abort(e.status_code)

    return render_template(
        "suppliers/dashboard.html",
        supplier=supplier,
        users=get_current_suppliers_users(),
        **template_data
    ), 200


@main.route('/edit', methods=['GET'])
@login_required
@flask_featureflags.is_active_feature('EDIT_SUPPLIER_PAGE')
def edit_supplier(supplier_form=None, contact_form=None, error=None):
    template_data = main.config['BASE_TEMPLATE_DATA']

    try:
        supplier = data_api_client.get_supplier(
            current_user.supplier_id
        )['suppliers']
    except APIError as e:
        abort(e.status_code)

    if supplier_form is None:
        supplier_form = EditSupplierForm(
            description=supplier['description'],
            clients=supplier['clients']
        )
        contact_form = EditContactInformationForm(
            prefix='contact_',
            **supplier['contactInformation'][0]
        )

    return render_template(
        "suppliers/edit_supplier.html",
        error=error,
        supplier_form=supplier_form,
        contact_form=contact_form,
        **template_data
    ), 200


@main.route('/edit', methods=['POST'])
@login_required
@flask_featureflags.is_active_feature('EDIT_SUPPLIER_PAGE')
def update_supplier():
    # FieldList expects post parameter keys to have number suffixes
    # (eg client-0, client-1 ...), which is incompatible with how
    # JS list-entry plugin generates input names. So instead of letting
    # the form search for request keys we pass in the values directly as data
    supplier_form = EditSupplierForm(
        formdata=None,
        description=request.form['description'],
        clients=filter(None, request.form.getlist('clients'))
    )

    contact_form = EditContactInformationForm(prefix='contact_')

    if not (supplier_form.validate_on_submit() and
            contact_form.validate_on_submit()):
        return edit_supplier(supplier_form=supplier_form,
                             contact_form=contact_form)

    try:
        data_api_client.update_supplier(
            current_user.supplier_id,
            supplier_form.data,
            current_user.email_address
        )

        data_api_client.update_contact_information(
            current_user.supplier_id,
            contact_form.id.data,
            contact_form.data,
            current_user.email_address
        )
    except APIError as e:
        return edit_supplier(supplier_form=supplier_form,
                             contact_form=contact_form,
                             error=e.message)

    return redirect(url_for(".dashboard"))


@main.route('/create', methods=['GET'])
def create_new_supplier():
    template_data = main.config['BASE_TEMPLATE_DATA']
    return render_template(
        "suppliers/create_new_supplier.html",
        **template_data
    ), 200


@main.route('/duns-number', methods=['GET'])
def duns_number():
    template_data = main.config['BASE_TEMPLATE_DATA']
    form = DunsNumberForm()

    if form.duns_number.name in session:
        form.duns_number.data = session[form.duns_number.name]

    return render_template(
        "suppliers/duns_number.html",
        form=form,
        **template_data
    ), 200


@main.route('/duns-number', methods=['POST'])
def submit_duns_number():
    form = DunsNumberForm()
    template_data = main.config['BASE_TEMPLATE_DATA']

    if form.validate_on_submit():
        session[form.duns_number.name] = form.duns_number.data
        return redirect(url_for(".companies_house_number"))
    else:
        return render_template(
            "suppliers/duns_number.html",
            form=form,
            **template_data
        ), 400


@main.route('/companies-house-number', methods=['GET'])
def companies_house_number():
    form = CompaniesHouseNumberForm()

    template_data = main.config['BASE_TEMPLATE_DATA']

    if form.validate_on_submit():
        return redirect(url_for(".company_name"))
    else:
        return render_template(
            "suppliers/companies_house_number.html",
            form=form,
            **template_data
        ), 400



@main.route('/company-name', methods=['GET'])
def company_name():
    form = CompanyNameForm()
    template_data = main.config['BASE_TEMPLATE_DATA']

    if form.validate_on_submit():
        return redirect(url_for(".company_contact_details"))
    else:
        return render_template(
            "suppliers/company_name.html",
            form=form,
            **template_data
        ), 400

@main.route('/company-contact-details', methods=['GET'])
def company_contact_details():
    form = CompanyContactDetailsForm()

    template_data = main.config['BASE_TEMPLATE_DATA']

    if form.validate_on_submit():
        return redirect(url_for(".company_summary"))
    else:
        return render_template(
            "suppliers/company_contact_details.html",
            form=form,
            **template_data
        ), 400


@main.route('/company-summary', methods=['GET'])
def company_summary():
    template_data = main.config['BASE_TEMPLATE_DATA']
    return render_template(
        "suppliers/company_summary.html",
        **template_data
    ), 200
