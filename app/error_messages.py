"""
Module with the api error messages
"""

# auth
no_auth_header_message = "Expected 'Authorization' header"
unbeary_auth_message = "Authorization header must start with 'Bearer '"
token_is_invalid_message = "Token is invalid: {0}"


#templating
invalid_compose_json = "Invalid compose json: {0}"
invalid_template_details = "Invalid template details: {0}"
template_already_exists = "Template '{0}' already exists in database"
invalid_directory_structure = "Template directories are invalid"
invalid_zip_file = "File must be of .zip type"
template_not_found = "Template '{0}' not found"
invalid_json_field = "JSON field is not valid: {0} "
unsupported_mime_type = "No supported format in ACCEPT header: {0}, Available formats: {1}"
aspect_ratio_compromised = "Specifying both width and height compromises the template's aspect ratio"
resizing_unsupported = "Resizing unsupported on provided mime_type: {0}"
single_page_unsupported = "Single page printing unsupported on provided mime_type: {0}"
negative_number_invalid = "A negative number is not allowed: {0}"
