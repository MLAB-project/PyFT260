# PyFT260

Welcome to PyFT260, a Python driver and interface library designed to control and interface with the FTDI FT260 chip, providing access to I2C, UART, and GPIO functionalities. PyFT260 aims to be a drop-in replacement for the smbus2 library (for I2C), offering extended support for the FT260's capabilities.

## Features

- **I2C Interface**: Communicate with I2C devices using the FT260 chip.
- **UART Interface**: Utilize the UART capabilities of the FT260 for serial communication. **NOT YET IMPLEMENTED**
- **GPIO Control**: Manage GPIO pins directly through the FT260. **NOT YET IMPLEMENTED**
- **Compatibility**: Designed as a drop-in replacement for smbus2, making it easy to switch and get the added benefits of FT260.

## FTDI FT260

The [FTDI FT260](https://www.ftdichip.com/old2020/Products/ICs/FT260.html) is a USB to UART/I2C bridge with an integrated Full Speed USB controller, built on the USB HID class specifically designed for bridging USB to UART and I2C interfaces. This chip simplifies USB to serial designs and significantly reduces external component count by fully integrating an internal USB 2.0 Hi-Speed IC and functionality for USB connectivity.

### Key Features of FT260:
- **USB 2.0 Full Speed compatible**
- **Integrated clock circuit requiring no external crystal**
- **Support for I2C and UART communication through USB**
- **Programmable control over GPIO pins**
- **Supports bus-powered and self-powered configurations**

These features make the FT260 an good choice for developing USB interface applications where you requires booth. UART and I2C interface. 


## Installation

You can install PyFT260 using pip:
```
  pip3 install ft260
```

