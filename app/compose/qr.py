from typing import List

from jmespath import search
from qrcode import make

from app.models.template import Template


def render_qr_codes(template: Template, output_folder: str, compose_data: dict) -> dict:
    """
    Render QR codes, altering compose_data to replace qr_code properties with the filepath to their renders

    Args:
        template: The Template being composed, used to look up its QR code schema paths
        output_folder: where to store the QR images renderer
        compose_data: the data to fill the template with

    Returns:
        dict: altered compose_data
    """
    qr_schema_paths = template.get_qr_entries()

    def set_nested(key_list: List[str], dict_: dict, value: str):
        """
        Sets dict_[key1, key2, ...] = value

        Args:
            key_list: Nested key list
            dict_: Dict to be iterated with key_list
            value: Value to be set
        """
        for key in key_list[:-1]:
            dict_ = dict_[key]
        dict_[key_list[-1]] = value

    for i, qr_schema_path in enumerate(qr_schema_paths):
        with open(f"{output_folder}/{i}.png", mode="wb") as qr_file:
            qr_value = search(qr_schema_path, compose_data)
            if qr_value is not None:
                img = make(qr_value)
                img.save(qr_file)
                set_nested(qr_schema_path.split("."), compose_data, qr_file.name)

    return compose_data
