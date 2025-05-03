from . import constants
from .packet import Packet


class DotsPicture(object):
    """Base class representing a DOTS PICTURE file.

    This class serves as a foundation for Small, Large, and RGB DOTS PICTURE files.
    """

    def __init__(self, label=None, height=0, width=0, max_height=31, max_width = 255, data=None, color_status="1000"):
        """
        :param label: File label (single character for Small/RGB, 9 chars for Large).
        :param height: Picture height in pixels.
        :param width: Picture width in pixels.
        :param data: Pixel data for the picture.
        :param color_status: Color status code ('1000' monochrome, '2000' 3-color, '4000' 8-color, '8000' RGB).
        """
        if label is None:
            # Default label might differ based on type, handle in child classes
            label = "?"
        if data is None:
            data = []
        height = abs(height)
        width = abs(width)
        self.max_height = max_height
        self.max_width = max_width
        if height > max_height:
            raise ValueError(f"{self.__class__.__name__} height cannot exceed {self.max_height} pixels.")
        if width > max_width:
            raise ValueError(f"{self.__class__.__name__} width cannot exceed {self.max_width} pixels.")

        self.label = label
        self.height = height
        self.width = width
        self.data = data  # Expecting a list of strings, one per row
        self.color_status = color_status # Used in memory allocation

    def _format_dimensions(self, num_bytes):
        """Formats height and width into the required number of hex bytes."""
        height_hex = ("%0" + str(num_bytes) + "X") % self.height
        width_hex = ("%0" + str(num_bytes) + "X") % self.width
        return height_hex+width_hex

    def _format_data(self):
        """Formats the pixel data rows with CR delimiters."""
        # Add CR (and optional LF) after each row
        # The protocol spec says last CR is optional, but sending it seems safer.
        # LF is ignored by the sign on read, so we won't add it here.
        formatted_rows = [row + constants.CR for row in self.data]
        return "".join(formatted_rows)

    def call(self):
        """Generate the control code sequence to call this picture from a TEXT file.

        Uses DC4 p [Picture Type] [File Label]
        Picture Type: '1' for Small, '2' for Large/RGB
        """
        # This might need adjustment based on specific picture type (Small vs Large/RGB)
        # Defaulting to Large/RGB for now, override in SmallDotsPicture
        picture_type_code = "2" 
        return "%sp%s%s" % (constants.DC4, picture_type_code, self.label)

    def __str__(self):
        # Actual packet generation will be handled by child classes
        raise NotImplementedError("Packet generation must be implemented in child classes.")

    def __repr__(self):
        return repr(self.__str__())

    def __bytes__(self):
        """Return the packet as bytes for Python 3 compatibility."""
        return bytes(self.__str__(), "ascii")




class SmallDotsPicture(DotsPicture):
    """Class representing a SMALL DOTS PICTURE file (up to 31x255).

    Inherits from DotsPicture.
    """

    def __init__(self, label="1", height=0, width=0, max_height=31, max_width = 255, data=None, color_status=constants.MONOSMALL):
        """
        :param label: File label (single character, default: "1").
        :param height: Picture height in pixels (0-31).
        :param width: Picture width in pixels (0-255).
        :param data: Pixel data (list of strings).
        :param color_status: Color status ("1000" mono, "2000" 3-color, "4000" 8-color).
        """

        if len(label) != 1:
            raise ValueError("SmallDotsPicture label must be a single character.")
        if color_status not in [constants.MONOSMALL, constants.THREESMALL, constants.EIGHTSMALL]:
            raise ValueError("SmallDotsPicture color status must be '1000', '2000', or '4000'.")

        super().__init__(label=label, height=height, width=width, max_height=max_height, max_width = max_width, data=data, color_status=color_status)
        
        # Height/Width are 2 ASCII hex bytes each
        self.size = self._format_dimensions(2)

    def call(self):
        """Generate the control code sequence to call this picture from a TEXT file."""
        # Uses [DC4][File Label]
        return "%s%s" % (constants.DC4, self.label)

    def __str__(self):
        """Generate the Write SMALL DOTS PICTURE packet string."""
        # Format: [WRITE_SMALL_DOTS][File Label][Height][Width][Row Data...]

        data_str = self._format_data()

        packet_data = "%s%s%s%s" % (
            constants.WRITE_SMALL_DOTS,
            self.label,
            self.size,
            data_str
        )
        return str(Packet(packet_data))


class LargeDotsPicture(DotsPicture):
    """Class representing a LARGE DOTS PICTURE file (up to 65535x65535).

    Inherits from DotsPicture.
    """

    def __init__(self, label="AAAAAAAAA", height=0, width=0, max_height=65535, max_width = 65535, data=None, color_status=constants.MONOLARGE):
        """
        :param label: File name (Nine ASCII characters, default: "AAAAAAAAA").
        :param height: Picture height in pixels (0-65535).
        :param width: Picture width in pixels (0-65535).
        :param data: Pixel data (list of strings).
        :param color_status: Color status ("01" mono, "02" 3-color, "04" 8-color, "08" RGB).
        """

        if len(label) != 9:
             # Enforcing 9 char based on E8 allocation spec
            raise ValueError("{self.__class__.__name__} name must be a 9 characters for E8 allocation.")
        if color_status not in [constants.MONOLARGE, constants.THREELARGE, constants.EIGHTLARGE, constants.RGB]:
            raise ValueError("LargeDotsPicture color status must be '01', '02', or '04'.")

        super().__init__(label=label, height=height, width=width, max_height=max_height, max_width = max_width, data=data, color_status=color_status)
        
        # Height/Width are 4 ASCII hex bytes each
        self.size = self._format_dimensions(4)

    def call(self):
        """Generate the control code sequence to call this picture from a TEXT file. Pg. 82

        Uses [US][Type][File name][display hold time]
        """

        return "%s%s%s%s" % (constants.US, "\x4C",self.label,"0000")

    def __str__(self):
        """Generate the Write LARGE DOTS PICTURE packet string."""
        # Format: [WRITE_LARGE_DOTS][File Label][Size (HeightWidth)][Row Data...]

        data_str = self._format_data()

        packet_data = "%s%s%s%s" % (
            constants.WRITE_LARGE_DOTS,
            self.label,
            self.size,
            data_str
        )
        return str(Packet(packet_data))


class RgbDotsPicture(LargeDotsPicture):
    """Class representing an RGB DOTS PICTURE file (up to 65535x65535).

    Inherits from DotsPicture.
    """

    def __init__(self, label="AAAAAAAAA", height=0, width=0, data=None, color_status=constants.RGB):
        """
        :param label: File label (single character, default: "R").
        :param height: Picture height in pixels (0-65535).
        :param width: Picture width in pixels (0-65535).
        :param data: Pixel data (list of strings, each char is 6 hex digits RRGGBB).
        """
        if color_status not in [constants.RGB]:
            raise ValueError("RGBDotsPicture color status must be '08'.")
        super().__init__(label=label, height=height, width=width, data=data, color_status=constants.RGB)

    # call() method inherited from LargeDotsPicture.

    def __str__(self):
        """Generate the Write RGB DOTS PICTURE packet string."""
        # Format: [WRITE_RGB_DOTS][File Label][Height][Width][Row Data...]
        # Height/Width are 4 ASCII hex bytes each
        # Row data consists of 6 hex chars (RRGGBB) per pixel
        # Todo: rgb compression
        data_str = self._format_data()

        packet_data = "%s%s%s%s" % (
            constants.WRITE_RGB_DOTS,
            self.label,
            self.size,
            data_str
        )
        return str(Packet(packet_data))

