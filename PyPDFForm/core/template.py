# -*- coding: utf-8 -*-
"""Contains helpers for template."""

import uuid
from typing import Dict, List, Tuple, Union

import pdfrw
from reportlab.pdfbase.pdfmetrics import stringWidth

from ..middleware.element import Element as ElementMiddleware
from ..middleware.element import ElementType
from . import constants
from .patterns import ELEMENT_KEY_PATTERNS, ELEMENT_TYPE_PATTERNS
from .utils import Utils


class Template:
    """Contains methods for interacting with a pdfrw parsed PDF form."""

    @staticmethod
    def remove_all_elements(pdf: bytes) -> bytes:
        """Removes all elements from a pdfrw parsed PDF form."""

        pdf = pdfrw.PdfReader(fdata=pdf)

        for page in pdf.pages:
            elements = page[constants.ANNOTATION_KEY]
            if elements:
                for j in reversed(range(len(elements))):
                    elements.pop(j)

        return Utils().generate_stream(pdf)

    @staticmethod
    def iterate_elements(
        pdf: Union[bytes, "pdfrw.PdfReader"], sejda: bool = False
    ) -> List["pdfrw.PdfDict"]:
        """Iterates through a PDF and returns all elements found."""

        if isinstance(pdf, bytes):
            pdf = pdfrw.PdfReader(fdata=pdf)

        result = []

        for page in pdf.pages:
            elements = page[constants.ANNOTATION_KEY]
            if elements:
                for element in elements:
                    if not sejda:
                        if (
                            element[constants.SUBTYPE_KEY]
                            == constants.WIDGET_SUBTYPE_KEY
                            and element[constants.ANNOTATION_FIELD_KEY]
                        ):
                            result.append(element)
                        elif (
                            element[constants.CHECKBOX_FIELD_VALUE_KEY]
                            and element[constants.PARENT_KEY]
                        ):
                            result.append(element)
                    else:
                        if (
                            element[constants.PARENT_KEY]
                            and element[constants.PARENT_KEY][
                                constants.ELEMENT_TYPE_KEY
                            ]
                        ):
                            result.append(element)

        return result

    @staticmethod
    def get_elements_by_page(
        pdf: Union[bytes, "pdfrw.PdfReader"], sejda: bool = False
    ) -> Dict[int, List["pdfrw.PdfDict"]]:
        """Iterates through a PDF and returns all elements found grouped by page."""

        if isinstance(pdf, bytes):
            pdf = pdfrw.PdfReader(fdata=pdf)

        result = {}

        for i, page in enumerate(pdf.pages):
            elements = page[constants.ANNOTATION_KEY]
            result[i + 1] = []
            if elements:
                for element in elements:
                    if not sejda:
                        if (
                            element[constants.SUBTYPE_KEY]
                            == constants.WIDGET_SUBTYPE_KEY
                            and element[constants.ANNOTATION_FIELD_KEY]
                        ):
                            result[i + 1].append(element)
                        elif (
                            element[constants.CHECKBOX_FIELD_VALUE_KEY]
                            and element[constants.PARENT_KEY]
                        ):
                            result[i + 1].append(element)
                    else:
                        if (
                            element[constants.PARENT_KEY]
                            and element[constants.PARENT_KEY][
                                constants.ELEMENT_TYPE_KEY
                            ]
                        ):
                            result[i + 1].append(element)

        return result

    def get_elements_by_page_v2(
        self, pdf: Union[bytes, "pdfrw.PdfReader"]
    ) -> Dict[int, List["pdfrw.PdfDict"]]:
        """Iterates through a PDF and returns all elements found grouped by page."""

        if isinstance(pdf, bytes):
            pdf = pdfrw.PdfReader(fdata=pdf)

        result = {}

        for i, page in enumerate(pdf.pages):
            elements = page[constants.ANNOTATION_KEY]
            result[i + 1] = []
            if elements:
                for element in elements:
                    for each in ELEMENT_TYPE_PATTERNS:
                        patterns = each[0]
                        check = True
                        for pattern in patterns:
                            check = check and self.find_pattern_match(pattern, element)
                        if check:
                            result[i + 1].append(element)
                            break

        return result

    @staticmethod
    def get_element_key(element: "pdfrw.PdfDict", sejda: bool = False) -> str:
        """Returns its annotated key given a PDF form element."""

        if sejda:
            return element[constants.PARENT_KEY][
                constants.ANNOTATION_FIELD_KEY
            ][1:-1]

        if not element[constants.ANNOTATION_FIELD_KEY]:
            return element[constants.PARENT_KEY][
                constants.ANNOTATION_FIELD_KEY
            ][1:-1]

        return element[constants.ANNOTATION_FIELD_KEY][1:-1]

    def traverse_pattern(
        self, pattern: dict, element: "pdfrw.PdfDict"
    ) -> Union[str, None]:
        """Traverses down a PDF dict pattern and find the value."""

        for key, value in element.items():
            result = None
            if key in pattern:
                if isinstance(pattern[key], dict) and isinstance(value, pdfrw.PdfDict):
                    result = self.traverse_pattern(pattern[key], value)
                else:
                    if pattern[key] is True and value:
                        return value
            if result:
                return result
        return None

    def get_element_key_v2(self, element: "pdfrw.PdfDict") -> Union[str, None]:
        """Finds a PDF element's annotated key by pattern matching."""

        for pattern in ELEMENT_KEY_PATTERNS:
            value = self.traverse_pattern(pattern, element)
            if value:
                return value[1:-1]

        return None

    @staticmethod
    def get_element_type(
        element: "pdfrw.PdfDict", sejda: bool = False
    ) -> Union["ElementType", None]:
        """Returns its annotated type given a PDF form element."""

        if sejda:
            if (
                element[constants.PARENT_KEY][
                    constants.ELEMENT_TYPE_KEY
                ]
                == constants.TEXT_FIELD_IDENTIFIER
            ):
                return ElementType.text
            if (
                element[constants.PARENT_KEY][
                    constants.ELEMENT_TYPE_KEY
                ]
                == constants.SELECTABLE_IDENTIFIER
            ):
                if (
                    element[constants.PARENT_KEY][
                        constants.SUBTYPE_KEY
                    ]
                    == constants.WIDGET_SUBTYPE_KEY
                ):
                    return ElementType.checkbox
                return ElementType.radio

        element_type_mapping = {
            constants.SELECTABLE_IDENTIFIER: ElementType.checkbox,
            constants.TEXT_FIELD_IDENTIFIER: ElementType.text,
        }

        result = element_type_mapping.get(
            str(element[constants.ELEMENT_TYPE_KEY])
        )

        if not result and element[constants.PARENT_KEY]:
            return ElementType.radio

        return result

    def find_pattern_match(self, pattern: dict, element: "pdfrw.PdfDict") -> bool:
        """Checks if a PDF dict pattern exists in a PDF element."""

        for key, value in element.items():
            result = False
            if key in pattern:
                if isinstance(pattern[key], dict) and isinstance(value, pdfrw.PdfDict):
                    result = self.find_pattern_match(pattern[key], value)
                else:
                    result = pattern[key] == value
            if result:
                return result
        return False

    def get_element_type_v2(
        self, element: "pdfrw.PdfDict"
    ) -> Union["ElementType", None]:
        """Finds a PDF element's annotated type by pattern matching."""

        for each in ELEMENT_TYPE_PATTERNS:
            patterns, _type = each
            check = True
            for pattern in patterns:
                check = check and self.find_pattern_match(pattern, element)
            if check:
                return _type

        return None

    @staticmethod
    def get_draw_checkbox_radio_coordinates(
        element: "pdfrw.PdfDict",
    ) -> Tuple[Union[float, int], Union[float, int]]:
        """Returns coordinates to draw at given a PDF form checkbox/radio element."""

        return (
            (
                float(element[constants.ANNOTATION_RECTANGLE_KEY][0])
                + float(element[constants.ANNOTATION_RECTANGLE_KEY][2])
            )
            / 2
            - 5,
            (
                float(element[constants.ANNOTATION_RECTANGLE_KEY][1])
                + float(element[constants.ANNOTATION_RECTANGLE_KEY][3])
            )
            / 2
            - 4,
        )

    @staticmethod
    def get_draw_checkbox_radio_coordinates_v2(
        element: "pdfrw.PdfDict",
        element_middleware: "ElementMiddleware",
    ) -> Tuple[Union[float, int], Union[float, int]]:
        """Returns coordinates to draw at given a PDF form checkbox/radio element."""

        string_height = element_middleware.font_size * 96 / 72
        width_mid_point = (
            float(element[constants.ANNOTATION_RECTANGLE_KEY][0])
            + float(element[constants.ANNOTATION_RECTANGLE_KEY][2])
        ) / 2
        height_mid_point = (
            float(element[constants.ANNOTATION_RECTANGLE_KEY][1])
            + float(element[constants.ANNOTATION_RECTANGLE_KEY][3])
        ) / 2

        return (
            width_mid_point
            - stringWidth(
                element_middleware.value,
                element_middleware.font,
                element_middleware.font_size,
            )
            / 2,
            (height_mid_point - string_height / 2 + height_mid_point) / 2,
        )

    @staticmethod
    def get_draw_text_coordinates(
        element: "pdfrw.PdfDict",
    ) -> Tuple[Union[float, int], Union[float, int]]:
        """Returns coordinates to draw text at given a PDF form text element."""

        x = float(element[constants.ANNOTATION_RECTANGLE_KEY][0])
        y = (
            float(element[constants.ANNOTATION_RECTANGLE_KEY][1])
            + float(element[constants.ANNOTATION_RECTANGLE_KEY][3])
        ) / 2 - 2

        return x, y

    @staticmethod
    def get_text_field_max_length(element: "pdfrw.PdfDict") -> Union[int, None]:
        """Returns the max length of the text field if presented or None."""

        return (
            int(element[constants.TEXT_FIELD_MAX_LENGTH_KEY])
            if constants.TEXT_FIELD_MAX_LENGTH_KEY in element
            else None
        )

    @staticmethod
    def is_text_field_comb(element: "pdfrw.PdfDict") -> bool:
        """Returns true if characters in a text field needs to be formatted into combs."""

        try:
            return "{0:b}".format(int(element["/Ff"]))[::-1][24] == "1"
        except IndexError:
            return False

    def assign_uuid(self, pdf: bytes) -> bytes:
        """Appends a separator and uuid after each element's annotated name."""

        _uuid = uuid.uuid4().hex

        pdf_file = pdfrw.PdfReader(fdata=pdf)

        for element in self.iterate_elements(pdf_file):
            base_key = self.get_element_key(element)
            existed_uuid = ""
            if constants.SEPARATOR in base_key:
                base_key, existed_uuid = base_key.split(constants.SEPARATOR)

            update_dict = {
                constants.ANNOTATION_FIELD_KEY.replace(
                    "/", ""
                ): f"{base_key}{constants.SEPARATOR}{existed_uuid or _uuid}"
            }
            element.update(pdfrw.PdfDict(**update_dict))

        return Utils().generate_stream(pdf_file)

    @staticmethod
    def get_char_rect_width(
        element: "pdfrw.PdfDict", element_middleware: "ElementMiddleware"
    ) -> float:
        """Returns rectangular width of each character for combed text fields."""

        rect_width = abs(
            float(element[constants.ANNOTATION_RECTANGLE_KEY][0])
            - float(element[constants.ANNOTATION_RECTANGLE_KEY][2])
        )
        return rect_width / element_middleware.max_length

    def get_character_x_paddings(
        self, element: "pdfrw.PdfDict", element_middleware: "ElementMiddleware"
    ) -> List[float]:
        """Returns paddings between characters for combed text fields."""

        length = min(len(element_middleware.value or ""), element_middleware.max_length)
        char_rect_width = self.get_char_rect_width(element, element_middleware)

        result = []

        current_x = 0
        for char in (element_middleware.value or "")[:length]:
            current_mid_point = current_x + char_rect_width / 2
            result.append(
                current_mid_point
                - stringWidth(
                    char, element_middleware.font, element_middleware.font_size
                )
                / 2
            )
            current_x += char_rect_width

        return result

    def get_draw_text_coordinates_v2(
        self, element: "pdfrw.PdfDict", element_middleware: "ElementMiddleware"
    ) -> Tuple[Union[float, int], Union[float, int]]:
        """Returns coordinates to draw text at given a PDF form text element."""

        length = (
            min(len(element_middleware.value or ""), element_middleware.max_length)
            if element_middleware.max_length is not None
            else len(element_middleware.value or "")
        )

        alignment = (
            element[constants.TEXT_FIELD_ALIGNMENT_IDENTIFIER] or 0
        )
        x = float(element[constants.ANNOTATION_RECTANGLE_KEY][0])

        if int(alignment) != 0:
            width_mid_point = (
                float(element[constants.ANNOTATION_RECTANGLE_KEY][0])
                + float(element[constants.ANNOTATION_RECTANGLE_KEY][2])
            ) / 2
            string_width = stringWidth(
                (element_middleware.value or "")[:length],
                element_middleware.font,
                element_middleware.font_size,
            )
            if element_middleware.comb is True and length:
                string_width = element_middleware.character_paddings[-1] + stringWidth(
                    element_middleware.value[:length][-1],
                    element_middleware.font,
                    element_middleware.font_size,
                )

            if int(alignment) == 1:
                x = width_mid_point - string_width / 2
            elif int(alignment) == 2:
                x = (
                    float(element[constants.ANNOTATION_RECTANGLE_KEY][2])
                    - string_width
                )
                if length > 0 and element_middleware.comb is True:
                    x -= (
                        self.get_char_rect_width(element, element_middleware)
                        - stringWidth(
                            element_middleware.value[-1],
                            element_middleware.font,
                            element_middleware.font_size,
                        )
                    ) / 2

        string_height = element_middleware.font_size * 96 / 72
        height_mid_point = (
            float(element[constants.ANNOTATION_RECTANGLE_KEY][1])
            + float(element[constants.ANNOTATION_RECTANGLE_KEY][3])
        ) / 2

        return (
            x
            - (
                element_middleware.character_paddings[0]
                + stringWidth(
                    element_middleware.value[:1],
                    element_middleware.font,
                    element_middleware.font_size,
                )
                / 2
                if (
                    element_middleware.comb is True
                    and length != 0
                    and length % 2 == 0
                    and int(alignment) == 1
                )
                else 0
            ),
            (height_mid_point - string_height / 2 + height_mid_point) / 2,
        )
