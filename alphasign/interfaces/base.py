import time

from .. import constants
from .. import packet

from ..string import String
from ..text import Text
from ..dots import SmallDotsPicture, LargeDotsPicture, RgbDotsPicture


class BaseInterface(object):
  """Base interface from which all other interfaces inherit.

  This class contains utility methods for fundamental sign features.
  """

  def write(self, data):
    return False

  def clear_memory(self):
    """Clear the sign's memory.

    :rtype: None
    """
    pkt = packet.Packet("%s%s" % (constants.WRITE_SPECIAL, "$"))
    self.write(pkt)
    time.sleep(1)

  def beep(self, frequency=0, duration=0.1, repeat=0):
    """Make the sign beep.

    :param frequency: frequency integer (not in Hz), 0 - 254
    :param duration: beep duration, 0.1 - 1.5
    :param repeat: number of times to repeat, 0 - 15

    :rtype: None
    """
    if frequency < 0:
      frequency = 0
    elif frequency > 254:
      frequency = 254

    duration = int(duration / 0.1)
    if duration < 1:
      duration = 1
    elif duration > 15:
      duration = 15

    if repeat < 0:
      repeat = 0
    elif repeat > 15:
      repeat = 15

    pkt = packet.Packet("%s%s%02X%X%X" % (constants.WRITE_SPECIAL, "(2",
                                          frequency, duration, repeat))
    self.write(pkt)

  def soft_reset(self):
    """Perform a soft reset on the sign.

    This is non-destructive and does not clear the sign's memory.

    :rtype: None
    """
    pkt = packet.Packet("%s%s" % (constants.WRITE_SPECIAL, ","))
    self.write(pkt)

  def allocate(self, files):
    """Allocate a set of files on the device.

    :param files: list of file objects (:class:`alphasign.text.Text`,
                                        :class:`alphasign.string.String`,
                                        :class:`alphasign.dots.SmallDotsPicture`,
                                        :class:`alphasign.dots.LargeDotsPicture`,
                                        :class:`alphasign.dots.RgbDotsPicture`, ...)

    :rtype: None
    """
    seq = ""
    for obj in files:
      # format: FTPSIZEQQQQ

      if type(obj) == String:
        file_type = "B"
        qqqq = "0000"  # unused for strings
        lock = constants.LOCKED
        size_hex = "%04X" % obj.size # Size is byte allocation
      elif type(obj) == Text:
        file_type = "A"
        qqqq = "FFFF"  # Default: Run always
        lock = constants.UNLOCKED
        size_hex = "%04X" % obj.size # Size is byte allocation
      elif isinstance(obj, (SmallDotsPicture, LargeDotsPicture, RgbDotsPicture)):
        file_type = "D"
        qqqq = obj.color_status # Color status (e.g., "1000", "2000", "4000", "8000")
        lock = constants.UNLOCKED # DOTS files are typically unlocked
        # SIZE for DOTS is RRCC (Rows Rows Cols Cols) in hex
        size_hex = "%02X%02X" % (obj.height, obj.width)
      else:
          # Optional: Handle unknown types or raise an error
          print(f"Warning: Unknown file type for allocation: {type(obj)}")
          continue # Skip unknown types

      alloc_str = ("%s%s%s%s%s" %
                   (obj.label,  # file label to allocate
                   file_type,   # file type
                   lock,
                   size_hex,    # size representation depends on type
                   qqqq))
      seq += alloc_str

    # allocate special TARGET TEXT files 1 through 5
    for i in range(5):
      alloc_str = ("%s%s%s%s%s" %
                   ("%d" % (i + 1),
                   "A",    # file type
                   constants.UNLOCKED,
                   "%04X" % 100, # Default size for target files
                   "FEFE")) # Default times for target files
      seq += alloc_str

    pkt = packet.Packet("%s%s%s" % (constants.WRITE_SPECIAL, "$", seq))
    self.write(pkt)

  def set_run_sequence(self, files, locked=False):
    """Set the run sequence on the device.

    This determines the order in which the files are displayed on the device, if
    at all. This is useful when handling multiple TEXT files.

    :param files: list of file objects (:class:`alphasign.text.Text`,
                                        :class:`alphasign.string.String`, ...)
    :param locked: allow sequence to be changed with IR keyboard

    :rtype: None
    """
    seq_str = ".T"
    seq_str += locked and "L" or "U"
    for obj in files:
      # Only include TEXT files in the run sequence
      if type(obj) == Text:
          seq_str += obj.label
    pkt = packet.Packet("%s%s" % (constants.WRITE_SPECIAL, seq_str))
    self.write(pkt)
