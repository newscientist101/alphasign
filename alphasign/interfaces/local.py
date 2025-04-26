from __future__ import print_function
import serial
import time
import usb.core
import usb.util

from alphasign.interfaces import base


class Serial(base.BaseInterface):
  """Connect to a sign through a local serial device.

  This class uses `pySerial <http://pyserial.sourceforge.net/>`_.
  """
  def __init__(self, device="/dev/ttyS0"):
    """
    :param device: character device (default: /dev/ttyS0)
    :type device: string
    """
    self.device = device
    self.debug = True
    self._conn = None

  def connect(self):
    """Establish connection to the device.
    """
    # TODO(ms): these settings can probably be tweaked and still support most of
    # the devices.
    self._conn = serial.Serial(port=self.device,
                               baudrate=4800,
                               parity=serial.PARITY_EVEN,
                               stopbits=serial.STOPBITS_TWO,
                               bytesize=serial.SEVENBITS,
                               timeout=1,
                               xonxoff=0,
                               rtscts=0)

  def disconnect(self):
    """Disconnect from the device.
    """
    if self._conn:
      self._conn.close()

  def write(self, packet):
    """Write packet to the serial interface.

    :param packet: packet to write
    :type packet: :class:`alphasign.packet.Packet`
    """
    if not self._conn or not self._conn.isOpen():
      self.connect()
    if self.debug:
      print("Writing packet: %s" % repr(packet))
    try:
      self._conn.write(str(packet).encode('utf-8'))
    except OSError:
      return False
    else:
      return True


class USB(base.BaseInterface):
  """Connect to a sign using USB.

  This class uses `PyUSB <https://github.com/pyusb/pyusb>`_.
  """
  def __init__(self, usb_id):
    """
    :param usb_id: tuple of (vendor id, product id) identifying the USB device
    """
    self.vendor_id, self.product_id = usb_id
    self.debug = False
    self._device = None
    self._read_endpoint = None
    self._write_endpoint = None

  def _get_device(self):
    """Find the USB device with the specified vendor and product ID.
    
    :return: USB device object or None if not found
    """
    device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
    return device

  def connect(self, reset=True):
    """Connect to the USB device.
    
    :param reset: send a USB RESET command to the sign.
                  This seems to cause problems in VMware.
    :exception usb.core.USBError: on USB-related errors
    """
    if self._device:
      return

    self._device = self._get_device()
    if not self._device:
      raise usb.core.USBError("Failed to find USB device %04x:%04x" %
                           (self.vendor_id, self.product_id))

    # Reset the device if requested
    if reset:
      try:
        self._device.reset()
      except Exception as e:
        print(f"Warning: Could not reset device: {e}")

    # Detach kernel driver if active
    if self._device.is_kernel_driver_active(0):
      try:
        self._device.detach_kernel_driver(0)
      except Exception as e:
        print(f"Warning: Could not detach kernel driver: {e}")

    # Set configuration
    try:
      self._device.set_configuration()
    except Exception as e:
      print(f"Warning: Could not set configuration: {e}")

    # Get configuration
    cfg = self._device.get_active_configuration()
    
    # Get interface
    intf = cfg[(0,0)]
    
    # Find endpoints
    for ep in intf:
        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
            self._read_endpoint = ep
        else:
            self._write_endpoint = ep
    
    if not self._write_endpoint:
        raise usb.core.USBError("Could not find write endpoint")

  def disconnect(self):
    """Disconnect from the USB device.
    """
    if self._device:
      try:
        usb.util.release_interface(self._device, 0)
        usb.util.dispose_resources(self._device)
      except Exception as e:
        print(f"Warning during disconnect: {e}")
      self._device = None
      self._read_endpoint = None
      self._write_endpoint = None

  def write(self, packet):
    """Write packet to the USB device.
    
    :param packet: packet to write
    :type packet: :class:`alphasign.packet.Packet`
    """
    if not self._device:
      self.connect()
    
    if self.debug:
      print("Writing packet: %s" % repr(packet))
    
    # Convert packet to bytes if it's not already
    packet_bytes = str(packet).encode('utf-8') if isinstance(packet, str) else bytes(packet)
    
    # Write the packet
    try:
      written = self._device.write(self._write_endpoint.bEndpointAddress, packet_bytes)
      if self.debug:
        print("%d bytes written" % written)
      
      # Send empty packet to finalize the transfer
      self._device.write(self._write_endpoint.bEndpointAddress, b'')
      return True
    except Exception as e:
      print(f"Error writing to USB device: {e}")
      return False


class DebugInterface(base.BaseInterface):
  """Dummy interface used only for debugging.

  This does nothing except print the contents of written packets.
  """
  def __init__(self):
    self.debug = True

  def connect(self):
    """ """
    pass

  def disconnect(self):
    """ """
    pass

  def write(self, packet):
    """ """
    if self.debug:
      print("Writing packet: %s" % repr(packet))
    return True
