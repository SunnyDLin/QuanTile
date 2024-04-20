# ------------------------------------------------------------------------------
# Module Name: state_vector_plot
#
# Description:
#   This module implements a display to plot Bloch Sphere to show quantum states.
#
# Platforms:
#   CPython3 on Raspberry Pi 2 and up, excluding Zero and Pico.
#   This module is intended to run on Raspberry Pi with display capability,
#   preferably a touch screen but not required.  However, some development can be
#   done on a Windows PC, except backend data and communication.
#   Windows PC is also supported.
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

import math
from dataclasses import dataclass

import numpy as np
import threading

from qiskit.visualization import plot_bloch_vector
import matplotlib.animation as animation
import matplotlib.pyplot as plt

from comm_util import Comm

import serial
import serial.tools.list_ports
from tkinter import ttk, messagebox
import tkinter as tk

import time

from qu_states import GateOperators, GateTypes
from ImageCache import ImageCache


@dataclass
class BlochSpherePoint:
    theta: float
    phi: float

    def __init__(self, theta_phi):
        self.theta = theta_phi[0]
        self.phi = theta_phi[1]


class SphereAlg:
    @staticmethod
    def sphericalToCartesian(point):
        # Convert spherical coordinates to Cartesian coordinates
        x = math.sin(point.theta) * math.cos(point.phi)
        y = math.sin(point.theta) * math.sin(point.phi)
        z = math.cos(point.theta)

        return np.array([x, y, z])

    @staticmethod
    def getNextPoint(start, destination):

        # # Convert spherical coordinates to Cartesian coordinates
        vec_start = SphereAlg.sphericalToCartesian(start)
        vec_dest = SphereAlg.sphericalToCartesian(destination)

        vec = vec_dest - vec_start
        magnitude = np.linalg.norm(vec)

        if magnitude < 0.05:  # if very close to destination, snap to it
            return destination

        if magnitude > 1.0:
            angularStep = 3.14 / 6.5
        elif magnitude > 0.5:
            angularStep = 3.14 / 10
        else:
            angularStep = 3.14 / 30

        vec_normal = np.cross(vec_start, vec_dest)
        vec_normal /= np.linalg.norm(vec_normal)
        vec_dir = np.cross(vec_normal, vec_start)
        vec_dir /= np.linalg.norm(vec_dir)
        vecNext = vec_start * np.cos(angularStep) + vec_dir * np.sin(angularStep)
        vecNext = vecNext / np.linalg.norm(vecNext)
        theta = np.arccos(vecNext[2])
        phi = np.arctan2(vecNext[1], vecNext[0])
        return BlochSpherePoint((theta, phi))


class StateVectorBlochPlot:
    animation = None    # object used to control animation (pause, resume, etc.)
    _fig = None
    _state_vectors = []
    _last_drawn_state_vectors = []
    _ax = []
    _key_lock = []
    _hide_vector = []
    _onComboBoxSelect = None  # callback function when a comboBox have a new selected item

    def setOnComboBoxSelectCallback(self, func):
        self._onComboBoxSelect = func

    @staticmethod
    def move_figure(fig, x, y):
        """Move figure's upper left corner to pixel (x, y)"""
        backend = plt.get_backend()
        if backend == 'TkAgg':
            fig.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))
        elif backend == 'WXAgg':
            fig.canvas.manager.window.SetPosition((x, y))
        else:
            # This works for QT and GTK
            # You can also use window.setGeometry
            fig.canvas.manager.window.move(x, y)

    # Constructor
    #   qubits (type:int) - number of Bloch spheres, range: 1~4
    #   interval (type:int) - minimum time interval between 2 animation frames
    def __init__(self, qubits=1, interval=200, instant_move=False):
        if qubits < 1 or qubits > 4:
            raise ValueError("Argument out of range, qubits:" + str(qubits))

        self._qubits = qubits
        self._interval = interval
        self._instant_move = instant_move

        width = 2 + self._qubits * 3
        height = 6

        self._fig = plt.figure(figsize=(width, height))
        self._fig.tight_layout(pad=1.0)

        StateVectorBlochPlot.move_figure(self._fig, 50, 5)

        plt.subplots_adjust(left=0.05, bottom=0.35, right=0.98, top=0.925,
                            wspace=0.1, hspace=0.1)
        # plt.subplot_tool()   # tool to adjust above parameters

        for i in range(qubits):
            self._state_vectors.append((0.0, 0.0))
            self._last_drawn_state_vectors.append((float("NaN"), float("NaN")))  # initializes to NaN
            self._key_lock.append(threading.Lock())
            self._hide_vector.append(False)

            ncols = qubits
            nrows = 1
            index = i + 1

            # create a subplot for a qubit
            subplot = self._fig.add_subplot(nrows, ncols, index, projection='3d')
            self._ax.append(subplot)
            self.zeroVector(i)

        # Create Configurator GUI components
        listOfGateTypes = [name for name in GateOperators.members()]  # used in combo box
        self.componentTypes = [GateTypes.UNDEFINED] * qubits
        self.comboBoxes = []
        self.symbols = []
        self.matrices = []

        # Crete labels
        label = tk.Label(text="Configurator:", background="white", font=("Helvetica", 15))
        label.place(x=30, rely=0.6)

        self.multiQubitEnabled = True

        def onButtonToggled(button):
            if self.multiQubitEnabled:
                button.config(text="Multi-qubit disabled", bg="#FFB6C1")
                self.multiQubitEnabled = False
            else:
                button.config(text="Multi-qubit enabled", bg="#90EE90")
                self.multiQubitEnabled = True

        toggleBtn = tk.Button(width=18, height=1, font=("Helvetica", 11))
        toggleBtn.place(relx=0.16, rely=0.95)
        toggleBtn.config(command=lambda: onButtonToggled(toggleBtn))
        onButtonToggled(toggleBtn)  # toggle the button to initialize it to off state

        def onComboBoxSelected(idx, combo_box):
            selected_item = combo_box.get()
            if self._onComboBoxSelect:
                self._onComboBoxSelect(idx, selected_item)
            else:
                print(f"Warning: Function _onComboBoxSelect is not set.")

        for i in range(qubits):
            x_pos = 0.01 + (0.2 + i) / self._qubits * 0.95
            portLabel = tk.Label(text="Port " + str(i),
                                 background="white", foreground="#0080ff", font=("Helvetica", 12, "bold"))
            portLabel.place(relx=x_pos, rely=0.65)

            comboBox = ttk.Combobox(values=listOfGateTypes, state="readonly", font=("Helvetica", 11))
            comboBox.place(relx=x_pos+0.2/qubits, rely=0.65, y=3)
            comboBox.bind("<<ComboboxSelected>>", lambda event, idx=i, cb=comboBox: onComboBoxSelected(idx, cb))
            self.comboBoxes.append(comboBox)

            # Create a space for symbol.
            symbol = tk.Label(background="white")
            symbol.place(relx=x_pos-0.01, rely=0.7)
            self.symbols.append(symbol)

            # crease a space for matrix
            symbol = tk.Label(background="white")
            symbol.place(relx=x_pos+0.3/qubits, rely=0.7)
            self.matrices.append(symbol)

    def __del__(self):
        plt.close(self._fig)

    def _redraw(self, frame):
        for i in range(self._qubits):
            with self._key_lock[i]:    # entering a critical section
                if self._last_drawn_state_vectors[i] == self._state_vectors[i]:
                    continue    # State vector did not change. No redraw is needed.

                if math.isnan(self._last_drawn_state_vectors[i][0]) \
                        or math.isnan(self._last_drawn_state_vectors[i][1]):
                    self._last_drawn_state_vectors[i] = 0.0, 0.0

                if self._instant_move:
                    nextPT = BlochSpherePoint(self._state_vectors[i])
                else:
                    startPT = BlochSpherePoint(self._last_drawn_state_vectors[i])
                    destinationPt = BlochSpherePoint(self._state_vectors[i])
                    nextPT = SphereAlg.getNextPoint(startPT, destinationPt)

                theta = nextPT.theta
                phi = nextPT.phi

                # draw a vector in Bloch sphere, using the existing ax and current projection
                self._ax[i].cla()  # Clear the current subplot without clearing the figure
                if not self._hide_vector[i]:
                    plot_bloch_vector([math.sin(theta) * math.cos(phi),
                                       math.sin(theta) * math.sin(phi),
                                       math.cos(theta)], ax=self._ax[i])
                else:
                    plot_bloch_vector([0.0, 0.0, 0.0], ax=self._ax[i])
                self._ax[i].title.set_text("qubit " + str(i))

                self._last_drawn_state_vectors[i] = theta, phi

    def start(self):
        # Create an animation
        # To avoid a possibly unbounded cache, frame data caching is disabled.
        self.animation = animation.FuncAnimation(self._fig, self._redraw,
                                                 interval=self._interval, cache_frame_data=False)

        # Display the animation
        plt.show()

    def close(self):
        if self._fig:
            plt.close(self._fig)

    def updateStateVector(self, vector, index=0):
        with self._key_lock[index]:    # entering a critical section
            self._hide_vector[index] = False
            self._state_vectors[index] = vector

    def zeroVector(self, index=0):
        with self._key_lock[index]:    # entering a critical section
            self._hide_vector[index] = True
            self._state_vectors[index] = (float("NaN"), float("NaN"))


# This function gets a base comm port number of a vendor specific device.
def getWinInitCommPort():
    ports = serial.tools.list_ports.comports()

    minCommID = math.inf
    for port in ports:
        if port.vid == 1027 and port.pid == 24593:     # The interface has a HEX VID:PID=0403:6011.
            commIndex = port.name.find("COM")
            if commIndex != -1:
                commID = int(port.name[commIndex + len("COM"):])
                if commID < minCommID:
                    minCommID = commID
    return minCommID


# Main program entrance to show Bloch Spheres
def main(qubits=4, commRequired=True, instant_move=False):
    # qubits: number of qubits to test, valid 1~4
    commPorts = []                         # Communication ports, each to the last tile of a qubit
    inputStateMissCount = [0] * qubits     # Counts of missing state inputs
    componentTypeMissCount = [0] * qubits  # Counts of missing component type responses
    maxQubits = 4       # limited by FT4232HL which supports up to 4 ports

    # Windows does not provide static comm ports.
    # This is a way to get a baseline port numbers.
    winInitCommPort = getWinInitCommPort()

    if commRequired:
        try:
            if winInitCommPort == math.inf:
                raise Exception("FT4232HL is not connected.")

            for i in range(qubits):
                portName = 'COM' + str(winInitCommPort + maxQubits - i - 1)  # makes the last comm port for qubit 0
                commPorts.append(Comm(portName))
                print("Qubit", i, " at serial port:", portName)

        except serial.serialutil.SerialException as e:
            print("Serial port open failure:", str(e))
            exit(1)

    blochPlot = StateVectorBlochPlot(qubits, instant_move=instant_move)

    def SetDefaultThetaPhi(proc_port):
        blochPlot.zeroVector(proc_port)
        blochPlot.componentTypes[proc_port] = GateTypes.UNDEFINED

        blochPlot.symbols[proc_port].config(image=None)
        blochPlot.symbols[proc_port].image = None  # Keep a reference to avoid garbage collection.
        blochPlot.matrices[proc_port].config(image=None)
        blochPlot.matrices[proc_port].image = None  # Keep a reference to avoid garbage collection.

    # This function gets theta and phi and updates a Bloch Sphere specified by plot_port.
    def updateInputStateCallback(theta, phi, plot_port):
        inputStateMissCount[plot_port] = 0
        blochPlot.updateStateVector((theta, phi), plot_port)

    imageCache = ImageCache()

    def updateGateTypeCallback(gate_type, plot_port):
        # update ComboBox GUI
        componentTypeMissCount[plot_port] = 0
        if blochPlot.componentTypes[plot_port] == gate_type:
            return
        blochPlot.componentTypes[plot_port] = gate_type

        name = GateTypes.name(gate_type)
        if name is not None:
            blochPlot.comboBoxes[plot_port].set(name)

            image = imageCache.getSymbolImage(name)
            blochPlot.symbols[plot_port].config(image=image)
            blochPlot.symbols[plot_port].image = image  # Keep a reference to avoid garbage collection.

            image = imageCache.getMatrixImage(name)
            blochPlot.matrices[plot_port].config(image=image)
            blochPlot.matrices[plot_port].image = image  # Keep a reference to avoid garbage collection.

    # Set up a thread to request data.
    requestRoutineRunning = False

    def requestRoutine():
        tick = 0

        procedurePortIndex = 0
        for channel in commPorts:
            channel.setUpdateInputStateCallback(updateInputStateCallback, procedurePortIndex)
            channel.setUpdateGateTypeCallback(updateGateTypeCallback, procedurePortIndex)
            procedurePortIndex += 1

        while requestRoutineRunning:
            procedurePortIndex = 0
            for channel in commPorts:
                try:
                    if tick % 2 == 0:
                        channel.sendStateRequest(channel.uart_in)
                        if inputStateMissCount[procedurePortIndex] >= 5:
                            SetDefaultThetaPhi(procedurePortIndex)
                        else:
                            inputStateMissCount[procedurePortIndex] += 1

                    if tick % 4 == 1:
                        channel.sendComponentTypeRequest(channel.uart_in)
                        if componentTypeMissCount[procedurePortIndex] >= 3:
                            blochPlot.comboBoxes[procedurePortIndex].set("")
                            blochPlot.componentTypes[procedurePortIndex] = GateTypes.UNDEFINED
                        else:
                            componentTypeMissCount[procedurePortIndex] += 1

                except serial.serialutil.SerialException as ex:
                    print("Communication failure:", str(ex))
                    plt.close()
                    exit(1)

                procedurePortIndex += 1

            time.sleep(0.025)
            tick += 1

        blochPlot.close()

    # Set up request thread before starting blochPlot.
    requestRoutineRunning = True
    requestRoutineThread = threading.Thread(target=requestRoutine)
    requestRoutineThread.start()

    multiQubitGateList = ["CONTROLLED_NOT", "CONTROLLED_Z", "SWAP", "TOFFOLI"]

    def show_info_dialog():
        messagebox.showinfo("Information", "Multi-qubit tile assignment is not fully supported.\n\n"
                                           "You may enable multi-qubit for demo purpose.\n"
                                           "Tiles lock up when it receives a multi-qubit assignment\n"
                                           "due to incompatibility with single-qubit tiles.")

    # This function is called when a
    def onComboBoxSelect(idx, selected_item):
        if not blochPlot.multiQubitEnabled and selected_item in multiQubitGateList:
            image = imageCache.getSymbolImage(selected_item)
            blochPlot.symbols[idx].config(image=image)
            blochPlot.symbols[idx].image = image  # Keep a reference to avoid garbage collection.

            image = imageCache.getMatrixImage(selected_item)
            blochPlot.matrices[idx].config(image=image)
            blochPlot.matrices[idx].image = image  # Keep a reference to avoid garbage collection.

            show_info_dialog()
            blochPlot.componentTypes[idx] = GateTypes.UNDEFINED  # set it UNDEFINED to allow update from tile
            return

        typeID = eval('GateTypes.' + selected_item).value
        print(f"comboBox{idx} item selected: {selected_item}, {typeID}")
        commPorts[idx].sendComponentTypeChangeRequest(typeID, commPorts[idx].uart_in)

    blochPlot.setOnComboBoxSelectCallback(onComboBoxSelect)

    # This starts the thread drawing Bloch Spheres.
    blochPlot.start()

    # Terminate threads and prepare exiting application.
    requestRoutineRunning = False
    for port in commPorts:
        port.messageServiceRoutineRunning = False
        port.stop()

    for port in commPorts:
        port.messageServiceThread.join()
    requestRoutineThread.join()

    exit(0)


if __name__ == '__main__':
    main(4, commRequired=True, instant_move=True)
