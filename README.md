# alphasign

alphasign is a Python library for
[Alpha American](http://www.alpha-american.com/) LED signs, such as the
[Betabrite](http://www.betabrite.com/). It implements the
[Alpha Communications Protocol](http://www.alpha-american.com/p-alpha-communications-protocol.html).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/msparks/alphasign.git
   ```
2. Navigate to the cloned directory:
   ```bash
   cd alphasign
   ```
3. Install the library using pip:
   ```bash
   pip install .
   ```

## Usage

Here is a simple example for controlling a Betabrite Prism via USB:

```python
import time
import alphasign


def main():
  sign = alphasign.USB(alphasign.devices.USB_BETABRITE_PRISM)
  sign.connect()
  sign.clear_memory()

  # create logical objects to work with
  counter_str = alphasign.String(size=14, label="1")
  counter_txt = alphasign.Text("counter value: %s%s" % (alphasign.colors.RED,
                                                        counter_str.call()),
                               label="A",
                               mode=alphasign.modes.HOLD)

  # allocate memory for these objects on the sign
  sign.allocate((counter_str, counter_txt))

  # tell sign to only display the counter text
  sign.set_run_sequence((counter_txt,))

  # write objects
  for obj in (counter_str, counter_txt):
    sign.write(obj)

  # (strictly) monotonically increasing counter
  counter_value = 0
  while True:
    counter_str.data = counter_value
    sign.write(counter_str)
    counter_value += 1
    time.sleep(1)


if __name__ == "__main__":
  main()
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

![Betabrite Prisom displaying the time and temperature updated by a program using the alphasign library.](http://farm9.staticflickr.com/8010/7151560649_2d5f04955b.jpg)

## License

This project is licensed under the BSD License.
