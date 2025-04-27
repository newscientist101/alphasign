from . import constants
from .packet import Packet


class DotsPicture(object):
    """Base class representing a DOTS PICTURE file.

    This class serves as a foundation for Small, Large, and RGB DOTS PICTURE files.
    """

    def __init__(self, label=None, height=0, width=0, data=None, color_status="1000"):
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

        self.label = label
        self.height = height
        self.width = width
        self.data = data  # Expecting a list of strings, one per row
        self.color_status = color_status # Used in memory allocation

        # Size attribute for allocation (rows << 16 | cols)
        # Use 4 bytes total for size in allocation, first 2 for rows, last 2 for cols
        self.size = (height << 16) | width

    def _format_dimensions(self, num_bytes):
        """Formats height and width into the required number of hex bytes."""
        height_hex = ("%0" + str(num_bytes) + "X") % self.height
        width_hex = ("%0" + str(num_bytes) + "X") % self.width
        return height_hex, width_hex

    def _format_data(self):
        """Formats the pixel data rows with CR delimiters."""
        # Add CR (and optional LF) after each row
        # The protocol spec says last CR is optional, but sending it seems safer.
        # LF is ignored by the sign on read, so we won't add it here.
        formatted_rows = [row + constants.CR for row in self.data]
        return "".join(formatted_rows)

    def call(self):
        """Generate the control code sequence to call this picture from a TEXT file.

        Uses ESC p [Picture Type] [File Label]
        Picture Type: '1' for Small, '2' for Large/RGB
        """
        # This might need adjustment based on specific picture type (Small vs Large/RGB)
        # Defaulting to Large/RGB for now, override in SmallDotsPicture
        picture_type_code = "2" 
        return "%sp%s%s" % (constants.ESC, picture_type_code, self.label)

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

    def __init__(self, label="1", height=0, width=0, data=None, color_status="1000"):
        """
        :param label: File label (single character, default: "1").
        :param height: Picture height in pixels (0-31).
        :param width: Picture width in pixels (0-255).
        :param data: Pixel data (list of strings).
        :param color_status: Color status ("1000" mono, "2000" 3-color, "4000" 8-color).
        """
        if height > 31:
            raise ValueError("SmallDotsPicture height cannot exceed 31 pixels.")
        if width > 255:
            raise ValueError("SmallDotsPicture width cannot exceed 255 pixels.")
        if len(label) != 1:
            raise ValueError("SmallDotsPicture label must be a single character.")

        super().__init__(label=label, height=height, width=width, data=data, color_status=color_status)
        # Allocation size uses 2 bytes for rows, 2 bytes for cols, even for small dots
        self.size = (height << 16) | width

    def call(self):
        """Generate the control code sequence to call this picture from a TEXT file."""
        # Uses ESC p 1 [File Label]
        return "%sp1%s" % (constants.ESC, self.label)

    def __str__(self):
        """Generate the Write SMALL DOTS PICTURE packet string."""
        # Format: [WRITE_SMALL_DOTS][File Label][Height][Width][Row Data...]
        # Height/Width are 2 ASCII hex bytes each
        height_hex, width_hex = self._format_dimensions(2)
        data_str = self._format_data()

        # Add 100ms delay note from protocol?
        # The protocol notes a 100ms delay needed after Width before Row Bit Pattern.
        # This library cannot enforce that delay directly during packet string generation.
        # Users of the library will need to handle delays if necessary, especially
        # between sending the allocation command and the write command, or potentially
        # splitting the write command (though the protocol implies it's one packet).
        # For now, just generate the packet data.

        packet_data = "%s%s%s%s%s" % (
            constants.WRITE_SMALL_DOTS,
            self.label,
            height_hex,
            width_hex,
            data_str
        )
        return str(Packet(packet_data))


class LargeDotsPicture(DotsPicture):
    """Class representing a LARGE DOTS PICTURE file (up to 65535x65535).

    Inherits from DotsPicture.
    """

    def __init__(self, label="A", height=0, width=0, data=None, color_status="1000"):
        """
        :param label: File label (single character, default: "A").
                      Note: Protocol doc is inconsistent (9 chars vs 1 char). Using 1 char for E$ allocation.
        :param height: Picture height in pixels (0-65535).
        :param width: Picture width in pixels (0-65535).
        :param data: Pixel data (list of strings).
        :param color_status: Color status ("1000" mono, "2000" 3-color, "4000" 8-color).
        """
        if height > 65535:
            raise ValueError("LargeDotsPicture height cannot exceed 65535 pixels.")
        if width > 65535:
            raise ValueError("LargeDotsPicture width cannot exceed 65535 pixels.")
        if len(label) != 1:
             # Enforcing single char based on E$ allocation spec, despite M command spec ambiguity
            raise ValueError("LargeDotsPicture label must be a single character for E$ allocation.")

        super().__init__(label=label, height=height, width=width, data=data, color_status=color_status)
        # Allocation size uses 2 bytes for rows, 2 bytes for cols
        self.size = (height << 16) | width

    # call() method inherited from DotsPicture uses picture type '2', which is correct for Large.

    def __str__(self):
        """Generate the Write LARGE DOTS PICTURE packet string."""
        # Format: [WRITE_LARGE_DOTS][File Label][Height][Width][Row Data...]
        # Height/Width are 4 ASCII hex bytes each
        height_hex, width_hex = self._format_dimensions(4)
        data_str = self._format_data()

        # Protocol notes 100ms delay after Width - see SmallDotsPicture comment.

        packet_data = "%s%s%s%s%s" % (
            constants.WRITE_LARGE_DOTS,
            self.label, # Using single char label here, matching allocation
            height_hex,
            width_hex,
            data_str
        )
        return str(Packet(packet_data))


class RgbDotsPicture(DotsPicture):
    """Class representing an RGB DOTS PICTURE file (up to 65535x65535).

    Inherits from DotsPicture.
    """

    def __init__(self, label="R", height=0, width=0, data=None):
        """
        :param label: File label (single character, default: "R").
        :param height: Picture height in pixels (0-65535).
        :param width: Picture width in pixels (0-65535).
        :param data: Pixel data (list of strings, each char is 6 hex digits RRGGBB).
        """
        if height > 65535:
            raise ValueError("RgbDotsPicture height cannot exceed 65535 pixels.")
        if width > 65535:
            raise ValueError("RgbDotsPicture width cannot exceed 65535 pixels.")
        if len(label) != 1:
            raise ValueError("RgbDotsPicture label must be a single character.")

        # Assuming '8000' is the correct status for RGB allocation via E$ or E8
        super().__init__(label=label, height=height, width=width, data=data, color_status="8000")
        # Allocation size uses 2 bytes for rows, 2 bytes for cols
        self.size = (height << 16) | width

    # call() method inherited from DotsPicture uses picture type '2', which is correct for RGB.

    def __str__(self):
        """Generate the Write RGB DOTS PICTURE packet string."""
        # Format: [WRITE_RGB_DOTS][File Label][Height][Width][Row Data...]
        # Height/Width are 4 ASCII hex bytes each
        # Row data consists of 6 hex chars (RRGGBB) per pixel
        height_hex, width_hex = self._format_dimensions(4)
        data_str = self._format_data()

        # Protocol notes 100ms delay after Width - see SmallDotsPicture comment.

        packet_data = "%s%s%s%s%s" % (
            constants.WRITE_RGB_DOTS,
            self.label,
            height_hex,
            width_hex,
            data_str
        )
        return str(Packet(packet_data))

