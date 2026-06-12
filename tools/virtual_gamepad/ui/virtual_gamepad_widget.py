import time

from lcm_msgs.data import GamepadKeys
from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.lcm_manager import LcmManager


class StatusLight(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.is_active = False
        self.blink_state = False
        self.blink_color = QColor("green")
        # Create the blinking timer.
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.setInterval(300)

    def toggle_blink(self):
        self.blink_state = not self.blink_state
        self.update()

    def set_active(self, active):
        self.is_active = active
        if active:
            self.blink_timer.start()
        else:
            self.blink_timer.stop()
            self.blink_state = False
        self.update()

    def set_blink_color(self, blink_color=QColor("green")):
        self.blink_color = blink_color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.is_active:
            color = self.blink_color if self.blink_state else QColor(
                128, 128, 128)
        else:
            color = QColor(128, 128, 128)

        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 16, 16)


class MacroButton(QPushButton):
    def __init__(self, text, button_combination, parent=None):
        super().__init__(text, parent)
        self.button_combination = button_combination

    def handle_click(self):
        print(f"Macro {self.text()} clicked, sending {self.button_combination}")


class GamepadButton(QPushButton):
    def __init__(self, text, button_index, parent=None, window=None):
        super().__init__(text, parent)
        self.button_index = button_index
        self.window = window
        self.setMinimumSize(20, 20)
        self.pressed.connect(self.handle_pressed)
        self.released.connect(self.handle_released)

    def handle_pressed(self):
        if self.window:
            self.window.button_state_changed(self.button_index, True)

    def handle_released(self):
        if self.window:
            self.window.button_state_changed(self.button_index, False)


class VirtualGamepadWidget(QWidget):
    STICK_KEYBOARD_STEP = 1

    def __init__(self):
        super().__init__()
        self.gamepad_keys = GamepadKeys()
        self.is_sending = False
        self.should_send_macro_count = 0
        self.motion_switch_pulse_queue = []
        # set keyboard shortcuts
        self.shortcuts = {
            'A': Qt.Key.Key_J,
            'B': Qt.Key.Key_K,
            'X': Qt.Key.Key_U,
            'Y': Qt.Key.Key_I,
            'LB': Qt.Key.Key_Q,
            'RB': Qt.Key.Key_E,
            'BACK': Qt.Key.Key_F1,
            'START': Qt.Key.Key_F2,
            'CROSS_X_UP': Qt.Key.Key_W,
            'CROSS_X_DOWN': Qt.Key.Key_S,
            'CROSS_Y_LEFT': Qt.Key.Key_A,
            'CROSS_Y_RIGHT': Qt.Key.Key_D
        }
        self.stick_shortcuts = {
            (Qt.Key.Key_Left, False): ("Left Stick Y", -self.STICK_KEYBOARD_STEP),
            (Qt.Key.Key_Right, False): ("Left Stick Y", self.STICK_KEYBOARD_STEP),
            (Qt.Key.Key_Up, False): ("Left Stick X", self.STICK_KEYBOARD_STEP),
            (Qt.Key.Key_Down, False): ("Left Stick X", -self.STICK_KEYBOARD_STEP),
            (Qt.Key.Key_Left, True): ("Right Stick Y", -self.STICK_KEYBOARD_STEP),
            (Qt.Key.Key_Right, True): ("Right Stick Y", self.STICK_KEYBOARD_STEP),
            (Qt.Key.Key_Up, True): ("Right Stick X", self.STICK_KEYBOARD_STEP),
            (Qt.Key.Key_Down, True): ("Right Stick X", -self.STICK_KEYBOARD_STEP),
        }

        enter_dance_sequence = [
            {"buttons": tuple(), "frames": 3},
            {"buttons": ("LB", "A"), "frames": 10},
            {"buttons": tuple(), "frames": 20},
            {"buttons": ("RB", "B"), "frames": 10},
            {"buttons": tuple(), "frames": 6},
        ]

        def enter_dance_then(buttons=tuple()):
            sequence = list(enter_dance_sequence)
            if buttons:
                sequence.extend(
                    [
                        {"buttons": buttons, "frames": 12},
                        {"buttons": tuple(), "frames": 3},
                    ]
                )
            return sequence

        # set predefined macro combinations
        self.macros = {
            "pd_stand: [LB, A]": ("LB", "A"),
            "passive: [LB, RB]": ("LB", "RB"),
            "walk: [LB, B]": ("LB", "B"),
            "walk forward: [LB, B] + L↑": [
                {"buttons": tuple(), "frames": 3},
                {"buttons": ("LB", "B"), "frames": 10},
                {"buttons": tuple(), "analog": {"Left Stick X": 0.6}, "frames": 80},
                {"buttons": tuple(), "analog": {"Left Stick X": 0.0}, "frames": 3},
            ],
            "dance: [LB,A] -> [RB,B]": enter_dance_then(),
            "dance punch": enter_dance_then(("A",)),
            "dance punch-fk": enter_dance_then(("A", "START")),
            "dance kick": enter_dance_then(("B",)),
            "dance riot": enter_dance_then(("X",)),
            "dance victory": enter_dance_then(("Y",)),
        }
        self.motion_switch_groups = (
            (
                "T800 83500 Dance Motions",
                (
                    ("Pause Toggle", ("BACK",)),
                    ("Punch", ("A",)),
                    ("Punch FK", ("A", "START")),
                    ("Kick Turn", ("B",)),
                    ("Riot Combo", ("X",)),
                    ("Victory", ("Y",)),
                ),
            ),
        )

        self.init_ui()

        self.button_map = {
            'A': (self.a_button, 2),
            'B': (self.b_button, 3),
            'X': (self.x_button, 4),
            'Y': (self.y_button, 5),
            'LB': (self.lb_button, 0),
            'RB': (self.rb_button, 1),
            'BACK': (self.back_button, 6),
            'START': (self.start_button, 7),
            'CROSS_X_UP': (self.up_button, 8),
            'CROSS_X_DOWN': (self.down_button, 9),
            'CROSS_Y_LEFT': (self.left_button, 10),
            'CROSS_Y_RIGHT': (self.right_button, 11)
        }

        self.analog_map = {
            "LT": (self.lt_slider, 0, self.lt_value_label),
            "RT": (self.rt_slider, 1, self.rt_value_label),
            "Left Stick X": (self.left_stick_x, 2, self.left_stick_x_label),
            "Left Stick Y": (self.left_stick_y, 3, self.left_stick_y_label),
            "Right Stick X": (self.right_stick_x, 4, self.right_stick_x_label),
            "Right Stick Y": (self.right_stick_y, 5, self.right_stick_y_label)
        }

        self.setup_shortcuts()
        self.setup_stick_shortcuts()
        self.setup_sliders()
        self.setup_macro_buttons()
        self.setup_motion_switch_buttons()
        # create timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_state)
        self.timer.setInterval(50)  # 20Hz
        LcmManager().add_connection_listener(self.on_lcm_status_changed)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        # set focus policy to ensure it can receive keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # LCM sending switch
        lcm_group = QGroupBox("LCM Sending")
        switch_layout = QHBoxLayout(lcm_group)
        switch_layout.addWidget(QLabel("Enable(F5):"))
        self.switch = QCheckBox()
        self.switch.stateChanged.connect(self.toggle_sending)
        switch_layout.addWidget(self.switch)

        self.lcm_enabled_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_F5), self)
        self.lcm_enabled_shortcut.activated.connect(self.switch.toggle)

        lcm_group.setMaximumHeight(100)
        # add stretch
        switch_layout.addStretch()
        # add status light
        self.status_light = StatusLight()
        switch_layout.addWidget(QLabel("Status:"))
        switch_layout.addWidget(self.status_light)

        switch_layout.addStretch()
        main_layout.addWidget(lcm_group)

        # main control area
        control_layout = QHBoxLayout()

        # left control
        left_group = QGroupBox("Left Control")
        left_layout = QVBoxLayout()

        # LT
        lt_layout = QHBoxLayout()
        lt_layout.addWidget(QLabel("LT"))
        self.lt_slider = QSlider(Qt.Orientation.Horizontal)
        # Use an integer range to represent 0.1 precision.
        self.lt_slider.setRange(-100, 100)
        self.lt_slider.setValue(0)
        self.lt_value_label = QLabel("0.0")
        lt_layout.addWidget(self.lt_slider)
        lt_layout.addWidget(self.lt_value_label)
        left_layout.addLayout(lt_layout)

        # LB
        self.lb_button = GamepadButton("LB(q)", 0, left_group, self)
        left_layout.addWidget(self.lb_button)

        # D-pad
        dpad_layout = QGridLayout()
        self.up_button = GamepadButton("↑(w)", 8, left_group, self)
        self.down_button = GamepadButton("↓(s)", 9, left_group, self)
        self.left_button = GamepadButton("←(a)", 10, left_group, self)
        self.right_button = GamepadButton("→(d)", 11, left_group, self)

        dpad_layout.addWidget(self.up_button, 0, 1)
        dpad_layout.addWidget(self.left_button, 1, 0)
        dpad_layout.addWidget(self.right_button, 1, 2)
        dpad_layout.addWidget(self.down_button, 2, 1)

        left_layout.addLayout(dpad_layout)
        left_group.setLayout(left_layout)
        control_layout.addWidget(left_group)

        # center control
        center_group = QGroupBox("Center Control")
        center_layout = QVBoxLayout()

        # Back/Start buttons
        back_start_layout = QHBoxLayout()
        self.back_button = GamepadButton("BACK(F1)", 6, center_group, self)
        self.start_button = GamepadButton("START(F2)", 7, center_group, self)
        back_start_layout.addWidget(self.back_button)
        back_start_layout.addWidget(self.start_button)
        center_layout.addLayout(back_start_layout)

        # Stick Controls Group
        stick_group = QGroupBox("Stick")
        stick_layout = QHBoxLayout()

        # Left Stick Group
        left_stick_group = QGroupBox("L (Arrow)")
        left_stick_layout = QVBoxLayout()

        # X axis for Left Stick
        left_stick_x_layout = QHBoxLayout()
        left_stick_x_layout.addWidget(QLabel("X"))
        self.left_stick_x = QSlider(Qt.Orientation.Horizontal)
        self.left_stick_x.setRange(-10, 10)
        self.left_stick_x.setValue(0)
        self.left_stick_x_label = QLabel("0.0")
        left_stick_x_layout.addWidget(self.left_stick_x)
        left_stick_x_layout.addWidget(self.left_stick_x_label)
        left_stick_layout.addLayout(left_stick_x_layout)

        # Y axis for Left Stick
        left_stick_y_layout = QHBoxLayout()
        left_stick_y_layout.addWidget(QLabel("Y"))
        self.left_stick_y = QSlider(Qt.Orientation.Horizontal)
        self.left_stick_y.setRange(-10, 10)
        self.left_stick_y.setValue(0)
        self.left_stick_y_label = QLabel("0.0")
        left_stick_y_layout.addWidget(self.left_stick_y)
        left_stick_y_layout.addWidget(self.left_stick_y_label)
        left_stick_layout.addLayout(left_stick_y_layout)

        left_stick_group.setLayout(left_stick_layout)
        stick_layout.addWidget(left_stick_group)

        # Right Stick Group
        right_stick_group = QGroupBox("R (Shift+Arrow)")
        right_stick_layout = QVBoxLayout()

        # X axis for Right Stick
        right_stick_x_layout = QHBoxLayout()
        right_stick_x_layout.addWidget(QLabel("X"))
        self.right_stick_x = QSlider(Qt.Orientation.Horizontal)
        self.right_stick_x.setRange(-10, 10)
        self.right_stick_x.setValue(0)
        self.right_stick_x_label = QLabel("0.0")

        right_stick_x_layout.addWidget(self.right_stick_x)
        right_stick_x_layout.addWidget(self.right_stick_x_label)
        right_stick_layout.addLayout(right_stick_x_layout)

        # Y axis for Right Stick
        right_stick_y_layout = QHBoxLayout()
        right_stick_y_layout.addWidget(QLabel("Y"))
        self.right_stick_y = QSlider(Qt.Orientation.Horizontal)
        self.right_stick_y.setRange(-10, 10)
        self.right_stick_y.setValue(0)
        self.right_stick_y_label = QLabel("0.0")

        right_stick_y_layout.addWidget(self.right_stick_y)
        right_stick_y_layout.addWidget(self.right_stick_y_label)
        right_stick_layout.addLayout(right_stick_y_layout)

        right_stick_group.setLayout(right_stick_layout)
        stick_layout.addWidget(right_stick_group)

        stick_group.setLayout(stick_layout)
        center_layout.addWidget(stick_group)
        center_group.setLayout(center_layout)
        control_layout.addWidget(center_group)

        # right control
        right_group = QGroupBox("Right Control")
        right_layout = QVBoxLayout()

        # RT
        rt_layout = QHBoxLayout()
        rt_layout.addWidget(QLabel("RT"))
        self.rt_slider = QSlider(Qt.Orientation.Horizontal)
        self.rt_slider.setRange(-100, 100)
        self.rt_slider.setValue(0)
        self.rt_value_label = QLabel("0.0")
        rt_layout.addWidget(self.rt_slider)
        rt_layout.addWidget(self.rt_value_label)
        right_layout.addLayout(rt_layout)

        # RB
        self.rb_button = GamepadButton("RB(e)", 1, right_group, self)
        right_layout.addWidget(self.rb_button)

        # ABXY buttons
        buttons_layout = QGridLayout()
        self.y_button = GamepadButton("Y(i)", 5, right_group, self)
        self.x_button = GamepadButton("X(u)", 4, right_group, self)
        self.b_button = GamepadButton("B(k)", 3, right_group, self)
        self.a_button = GamepadButton("A(j)", 2, right_group, self)

        buttons_layout.addWidget(self.y_button, 0, 1)
        buttons_layout.addWidget(self.x_button, 1, 0)
        buttons_layout.addWidget(self.b_button, 1, 2)
        buttons_layout.addWidget(self.a_button, 2, 1)

        right_layout.addLayout(buttons_layout)
        right_group.setLayout(right_layout)
        control_layout.addWidget(right_group)

        main_layout.addLayout(control_layout)

        # macro buttons group (bottom)
        macro_group = QGroupBox("Quick Macros")
        self.macro_layout = QVBoxLayout()
        macro_group.setLayout(self.macro_layout)
        main_layout.addWidget(macro_group)

        motion_group = QGroupBox("Dance Motion Switch")
        self.motion_switch_layout = QVBoxLayout()
        motion_group.setLayout(self.motion_switch_layout)
        main_layout.addWidget(motion_group)

        # self.setMinimumSize(1200, 800)

    def setup_macro_buttons(self):
        # clear all child items in the macro button layout
        while self.macro_layout.count():
            item = self.macro_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # If the child is a layout, recursively clear all of its items.
                layout = item.layout()
                while layout.count():
                    layout_item = layout.takeAt(0)
                    if layout_item.widget():
                        layout_item.widget().deleteLater()

        # Show at most four buttons per row.
        MAX_BUTTONS_PER_ROW = 4
        current_row_layout = None
        button_count_in_current_row = 0

        for name, combination in self.macros.items():
            macro_button = MacroButton(name, combination, self)
            macro_button.clicked.connect(
                lambda clicked, btn=macro_button: self.handle_macro_button_pressed(clicked, btn))

            # if current row is full or no row layout is created, create a new row layout
            if button_count_in_current_row >= MAX_BUTTONS_PER_ROW or current_row_layout is None:
                current_row_layout = QHBoxLayout()
                self.macro_layout.addLayout(current_row_layout)
                button_count_in_current_row = 0

            # Add the button to the current row.
            current_row_layout.addWidget(macro_button)
            button_count_in_current_row += 1

        # Add stretch to the end of the last row.
        if current_row_layout and button_count_in_current_row < MAX_BUTTONS_PER_ROW:
            current_row_layout.addStretch()

    def setup_motion_switch_buttons(self):
        while self.motion_switch_layout.count():
            item = self.motion_switch_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for group_name, switches in self.motion_switch_groups:
            group = QGroupBox(group_name)
            group_layout = QHBoxLayout(group)
            for name, combination in switches:
                button = MacroButton(name, combination, self)
                button.clicked.connect(
                    lambda clicked, btn=button: self.handle_motion_switch_button_pressed(clicked, btn))
                group_layout.addWidget(button)
            group_layout.addStretch()
            self.motion_switch_layout.addWidget(group)
        self.motion_switch_layout.addStretch()
        self.motion_switch_layout.addStretch()

    def on_lcm_status_changed(self, connected):
        if connected:
            self.status_light.set_active(self.is_sending)
        else:
            print("Virtual Gamepad disconnected from LCM")
            self.status_light.set_active(False)

    def slider_changed(self, slider, label, analog_id):
        # Convert the slider value to the range [-1.0, 1.0].
        value = slider.value() / 10.0
        # Update the label with one decimal place.
        label.setText(f"{value:.1f}")
        # Forward the converted value to the analog state handler.
        self.analog_changed(analog_id, value)

    def toggle_sending(self, state):
        self.is_sending = bool(state)
        self.discard_pending_inputs()
        self.status_light.set_active(self.is_sending and LcmManager().is_connected())
        if self.is_sending:
            self.timer.start()
        else:
            self.timer.stop()

    def convert_button_combination_to_gamepad_keys(self, button_combination):
        gamepad_keys = GamepadKeys()
        # Copy the current analog state.
        for i in range(len(gamepad_keys.analog_states)):
            gamepad_keys.analog_states[i] = self.gamepad_keys.analog_states[i]

        analog_overrides = {}
        if isinstance(button_combination, dict):
            analog_overrides = button_combination.get("analog", {})
            button_combination = button_combination.get("buttons", tuple())

        # Set digital button states.
        for button_name in button_combination:
            if button_name in self.button_map:
                button, index = self.button_map[button_name]
                gamepad_keys.digital_states[index] = 1
            else:
                print(f"Warning: Button {button_name} not found in button_map")

        for analog_name, value in analog_overrides.items():
            if analog_name in self.analog_map:
                _, index, _ = self.analog_map[analog_name]
                gamepad_keys.analog_states[index] = value
            elif isinstance(analog_name, int) and 0 <= analog_name < len(gamepad_keys.analog_states):
                gamepad_keys.analog_states[analog_name] = value
            else:
                print(f"Warning: Analog {analog_name} not found in analog_map")
        return gamepad_keys

    def setup_shortcuts(self):
        self.shortcut_states = {name: False for name in self.shortcuts}
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def setup_stick_shortcuts(self):
        self.active_stick_keys = {}

    def setup_sliders(self):
        for name, (slider, analog_id, label) in self.analog_map.items():
            slider: QSlider
            slider.valueChanged.connect(
                lambda v, s=slider, l=label, a=analog_id: self.slider_changed(
                    s, l, a)
            )

    def adjust_stick_value(self, analog_name, delta):
        slider, _, _ = self.analog_map[analog_name]
        next_value = max(slider.minimum(),
                         min(slider.maximum(), delta * 10))
        slider.setValue(next_value)

    def reset_stick_values(self):
        for analog_name in (
            "Left Stick X",
            "Left Stick Y",
            "Right Stick X",
            "Right Stick Y",
        ):
            slider, _, _ = self.analog_map[analog_name]
            slider.setValue(0)

    def discard_pending_inputs(self):
        self.gamepad_keys = GamepadKeys()
        self.should_send_macro_count = 0
        self.motion_switch_pulse_queue = []
        self.shortcut_states = {name: False for name in self.shortcuts}

        for button, _ in self.button_map.values():
            button.setDown(False)

        for slider, _, _ in self.analog_map.values():
            slider.setValue(0)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            return self.handle_keyboard_event(event, True)
        if event.type() == QEvent.Type.KeyRelease:
            return self.handle_keyboard_event(event, False)
        return super().eventFilter(obj, event)

    def handle_keyboard_event(self, event, pressed):
        if event.isAutoRepeat():
            return True

        reverse_shortcuts = {v: k for k, v in self.shortcuts.items()}
        if event.key() in reverse_shortcuts:
            button_name = reverse_shortcuts[event.key()]
            if pressed:
                self.handle_shortcut_pressed(button_name)
            else:
                self.handle_shortcut_released(button_name)
            return True

        if event.key() == Qt.Key.Key_Space:
            if pressed:
                self.reset_stick_values()
            return True

        shift_pressed = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        stick_target = self.stick_shortcuts.get((event.key(), shift_pressed))
        if stick_target:
            analog_name, delta = stick_target
            if pressed:
                self.active_stick_keys[event.key(), shift_pressed] = analog_name
                self.adjust_stick_value(analog_name, delta)
            else:
                self.active_stick_keys.pop((event.key(), shift_pressed), None)
                self.reset_stick_axis_if_released(analog_name)
            return True

        return False

    def reset_stick_axis_if_released(self, analog_name):
        if analog_name in self.active_stick_keys.values():
            return
        slider, _, _ = self.analog_map[analog_name]
        slider.setValue(0)

    def keyPressEvent(self, event):
        if not self.handle_keyboard_event(event, True):
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not self.handle_keyboard_event(event, False):
            super().keyReleaseEvent(event)

    def handle_shortcut_pressed(self, button_name):
        if not self.shortcut_states.get(button_name, False):
            self.shortcut_states[button_name] = True
            self.handle_shortcut(button_name, True)

    def handle_shortcut_released(self, button_name):
        if self.shortcut_states.get(button_name, False):
            self.shortcut_states[button_name] = False
            self.handle_shortcut(button_name, False)

    def handle_shortcut(self, button_name, pressed):
        if button_name in self.button_map:
            button, index = self.button_map[button_name]
            button.setDown(pressed)
            self.button_state_changed(index, pressed)

    def handle_macro_button_pressed(self, clicked, macro_button: MacroButton):
        if not self.is_sending:
            return
        if isinstance(macro_button.button_combination, list):
            self.should_send_macro_count = 0
            self.motion_switch_pulse_queue = []
            for frame in macro_button.button_combination:
                self.motion_switch_pulse_queue.extend([frame] * frame.get("frames", 1))
            return
        MACRO_BUTTON_SENDING_COUNT = 10
        self.should_send_macro_count = MACRO_BUTTON_SENDING_COUNT
        self.marcro_button_combination = macro_button.button_combination

    def handle_motion_switch_button_pressed(self, clicked, macro_button: MacroButton):
        if not self.is_sending:
            return
        release_frames = [tuple()] * 3
        press_frames = [macro_button.button_combination] * 10
        trailing_release_frames = [tuple()] * 2
        self.motion_switch_pulse_queue = release_frames + press_frames + trailing_release_frames

    def button_state_changed(self, index, pressed):
        if not self.is_sending:
            return
        self.gamepad_keys.digital_states[index] = 1 if pressed else 0

    def analog_changed(self, index, value):
        if not self.is_sending:
            return
        self.gamepad_keys.analog_states[index] = value

    def send_state(self):
        if not self.is_sending:
            return

        lcm_handle = LcmManager().lcm_handle
        if not lcm_handle:
            self.status_light.set_active(False)
            return

        if self.motion_switch_pulse_queue:
            gamepad_keys = self.convert_button_combination_to_gamepad_keys(
                self.motion_switch_pulse_queue.pop(0))
        elif self.should_send_macro_count > 0:
            self.should_send_macro_count -= 1
            # Create a fresh gamepad state for macro button playback.
            gamepad_keys = self.convert_button_combination_to_gamepad_keys(
                self.marcro_button_combination)
        else:
            gamepad_keys = self.gamepad_keys

        # Always refresh the timestamp before publishing.
        gamepad_keys.timestamp = int(time.time() * 1_000_000)

        lcm_handle.publish("virtual_gamepad/gamepad_keys", gamepad_keys.encode())

        # Update the status light color based on the current input state.
        if all(x == 0 for x in gamepad_keys.digital_states) and all(abs(x) < 1e-6 for x in gamepad_keys.analog_states):
            self.status_light.set_blink_color()
        else:
            self.status_light.set_blink_color(QColor("orange"))

    def closeEvent(self, event):
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        LcmManager().remove_connection_listener(self.on_lcm_status_changed)
        super().closeEvent(event)

    def print_state(self, gamepad_keys):
        analog_values = ''
        for name, (slider, analog_id, label) in self.analog_map.items():
            analog_values += f"{name}: {gamepad_keys.analog_states[analog_id]:.6f}, "
        print(f"[{analog_values}]")
        digital_values = ''
        for name, (button, index) in self.button_map.items():
            digital_values += f"{name}: {gamepad_keys.digital_states[index]}, "
        print(f"[{digital_values}]")
