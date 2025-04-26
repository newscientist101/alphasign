from . import constants
from . import modes
from . import positions
from .packet import Packet


class RGB(object):
  """Class representing a RGB DOTS PICTURE file.

  This class is aliased as :class:`alphasign.RGB` in :mod:`alphasign.__init__`.
  """

  def __init__(self, data=None, label=None, size=None,
               height=None, width=None, bitPattern=None, priority=False):
    """
    :param data: initial string to insert into object
    :param label: file label (default: "A")
    :param size: amount of bytes to allocate for object on sign (default: 64)
    :param priority: set this text to be displayed instead of
                     all other TEXT files. Set to True with an empty message to
                     clear a priority TEXT.
    """
    if data is None:
      data = ""
    if label is None:
      label = "A"
    if size is None:
      size = 1024
    if len(data) > size:
      size = len(data)
    if size > 1024:
      size = 1024
    if size < 1:
      size = 1
    if position is None:
      position = positions.MIDDLE_LINE
    if mode is None:
      mode = modes.ROTATE

    self.label = label
    self.size = size
    self.data = data
    self.priority = priority

  def __str__(self):
    # [WRITE_RGB_DOTS][File Label]

    if self.data:
      packet = Packet("%s%s%s%s%s%s" % (constants.WRITE_RGB_DOTS,
                                        (self.priority and "0" or self.label),
                                        self.data))
    else:
      packet = Packet("%s%s" % (constants.WRITE_RGB_DOTS,
                                (self.priority and "0" or self.label)))
    return str(packet)

  def __repr__(self):
    return repr(self.__str__())
    
  def __bytes__(self):
    """Return the packet as bytes for Python 3 compatibility."""
    if self.data:
      packet = Packet("%s%s%s%s%s%s" % (constants.WRITE_RGB_DOTS,
                                        (self.priority and "0" or self.label),
                                        self.data))
    else:
      packet = Packet("%s%s" % (constants.WRITE_RGB_DOTS,
                                (self.priority and "0" or self.label)))
    return bytes(packet)
