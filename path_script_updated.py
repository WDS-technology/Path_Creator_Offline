import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk

import json
import paramiko
import re


class FlightPlannerApp(tk.Tk):
    """
    This method sets up the main window, including its title and size.
    It initializes two canvases: one for the XY plane (self.canvas) and another for the Z axis
    (self.canvas_z). It also creates a frame for command buttons and initializes
    a dictionary with several properties related to the points and commands to be used in the flight path.
    """

    def __init__(self):
        super().__init__()
        self.title("Flight Planner")
        self.geometry("850x850")  # Increased size for better view

        self.canvas = tk.Canvas(
            self, bg="white", width=500, height=500
        )  # Tkinter Canvas widget
        self.canvas.pack(pady=(20, 10))
        self.draw_grid()

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Coordinate canvas
        # FLY_TO_Z canvas
        self.canvas_z = tk.Canvas(
            self, width=400, height=200, bg="white"
        )  # Tkinter Canvas widget
        self.canvas_z.pack(pady=(60, 20))
        self.draw_grid_z()
        self.command_frame = ttk.Frame(
            self
        )  # widget that serves as a container for command buttons
        self.command_frame.pack(pady=(0, 10))
        # self.command_frame.pack(side=tk.RIGHT, pady=20)
        self.command_frame.place(
            x=420, y=540, anchor="n"
        )  # Place the frame at 250 pixels from the top and to the far right
        self.point_counter = (
            0  # Used to manage the indexing and scaling of points, on the Z canvas.
        )
        self.expected_total_points = (
            10  # this is used to manage the scaling of the Z axis - expects
        )
        self.last_z_value = 0  # default starting value

        # A dictionary mapping button labels to their respective command types
        self.command_buttons_row1 = {
            "Fly to Z": "SCHEDULE_FLY_TO_Z",
            "Return to Start": "SCHEDULE_RETURN_TO_TAKEOFF_POSITION",
            "Fly to XY": "SCHEDULE_FLY_TO_XY",
            "Fly to XYZ": "SCHEDULE_MOVE_XYZ",
        }

        self.command_buttons_row2 = {
            "Delay": "SCHEDULE_WAIT_FOR_PERIOD",
            "Set XY Speed": "SCHEDULE_SET_XY_SPEED",
            "Set Yaw": "SCHEDULE_FLY_TO_YAW",
            "Take Picture": "SCHEDULE_TAKE_PICTURE",
            "Start Recording": "SCHEDULE_SET_PAYLOAD_RECORDING",
        }
        # Creating subframes for two rows of buttons
        self.command_frame_row1 = ttk.Frame(self.command_frame)
        self.command_frame_row1.pack(side=tk.TOP, fill=tk.X)

        self.command_frame_row2 = ttk.Frame(self.command_frame)
        self.command_frame_row2.pack(side=tk.TOP, fill=tk.X)

        # Populate row 1 with buttons
        # Populate row 1 with buttons
        for label, command in self.command_buttons_row1.items():
            btn = ttk.Button(
                self.command_frame_row1,
                text=label,
                command=lambda cmd=command: self.add_command(cmd),  # Fix applied here
            )
            btn.pack(side=tk.LEFT, padx=5)

        # Populate row 2 with buttons
        for label, command in self.command_buttons_row2.items():
            btn = ttk.Button(
                self.command_frame_row2,
                text=label,
                command=lambda cmd=command: self.add_command(cmd),  # Fix applied here
            )
            btn.pack(side=tk.LEFT, padx=5)

        self.btn_export = ttk.Button(
            self, text="Export to JSON", command=self.export_to_json
        )
        self.btn_export.pack(
            side=tk.TOP, pady=20
        )  # Stack this button below the previous buttons

        self.path_points = (
            []
        )  # A list  stores dictionaries representing each point in the flight path, inclu type, arguments, and canvas coordinates.
        self.draw_axis_names()

    """
    These methods draw grid lines on the canvases for better 
    visualization of the XY plane and Z axis."""

    def draw_grid(self):
        # Define the number of ticks based on the area and tick size
        # 250 meters with each tick representing 10 meters
        tick_spacing = 20  # pixels per tick, for simplicity in visualization
        num_ticks = (
            250 // 10
        )  # Number of ticks to represent 250 meters with each tick being 10 meters
        # Draw grid lines based on the tick spacing
        for i in range(num_ticks + 1):  # +1 to include the last line at the edge
            # Calculate position for each line
            pos = i * tick_spacing
            self.canvas.create_line(pos, 0, pos, 500, fill="gray")  # Vertical lines
            self.canvas.create_line(0, pos, 500, pos, fill="gray")  # Horizontal lines

        # Draw center point (optional, depending on your needs)
        self.canvas.create_oval(245, 245, 255, 255, fill="red")

    """
    These methods draw grid lines on the canvases for better 
    visualization of the XY plane and Z axis."""

    def draw_grid_z(self):
        for i in range(50, 401, 25):
            self.canvas_z.create_line(i, 0, i, 200, dash=(2, 2))
            self.canvas_z.create_line(0, i, 400, i, dash=(2, 2))

    def meters_to_pixels(self, x_meters, y_meters):
        scale = 2  # 2 pixels per meter because 500 pixels cover 250 meters
        # Convert meters to pixels
        x_pixels = x_meters * scale
        y_pixels = y_meters * scale
        # Adjust for canvas origin to make (0,0) meters at the center of the canvas
        x_center_offset = 250  # Center of the canvas in pixels (if canvas is 500x500)
        y_center_offset = 250  # Same as above
        # Adjust x normally since positive x is right
        x_adjusted = x_center_offset + x_pixels
        # Invert y since positive y should go up (canvas y increases downwards)
        y_adjusted = y_center_offset - y_pixels  # Subtract to invert y-axis
        return x_adjusted, y_adjusted

    """
    Adds a command to the last plotted point. 
    It's used for adding commands via button clicks in the UI.
    """

    def add_command(self, command):

        # Default values for the canvas coordinates
        x_for_canvas, y_for_canvas = self.meters_to_pixels(0, 0)

        if len(self.path_points) == 0 and command not in [
            "SCHEDULE_FLY_TO_Z",
            "SCHEDULE_MOVE_XYZ",
        ]:  # If there are no points on the canvas
            return

        # Get arguments for the specific command
        arguments = self.get_command_arguments(command)
        if not arguments:  # User closed the dialog or pressed cancel
            return

        if command in [
            "SCHEDULE_MOVE_XYZ",
            "SCHEDULE_FLY_TO_XY",
            "SCHEDULE_RETURN_TO_TAKEOFF_POSITION",
        ]:
            x_from_user = arguments.get("x", 0)
            y_from_user = arguments.get("y", 0)
            x_for_canvas, y_for_canvas = self.meters_to_pixels(
                x_from_user, y_from_user
            )  # Convert meters to pixels

            if command == "SCHEDULE_MOVE_XYZ":
                z_value = arguments.get("z", 0)

        elif command in [
            "SCHEDULE_FLY_TO_Z",
            "SCHEDULE_FLY_TO_YAW",
            "SCHEDULE_WAIT_FOR_PERIOD",
            "SCHEDULE_SET_XY_SPEED",
        ]:
            # Use the last known XY if available
            if len(self.path_points) > 0:
                last_point = self.path_points[-1]
                x_for_canvas, y_for_canvas = last_point["canvas_coordinates"]

        if command in ["SCHEDULE_FLY_TO_Z", "SCHEDULE_MOVE_XYZ", "SCHEDULE_MOVE_XYZ"]:
            z_value = arguments.get("z", 0)

            # Convert and plot Z value on Z canvas, even if it's the first command
            x_scaled_for_z_canvas, y_scaled_for_z_canvas = (
                self.plot_z_value_on_canvas_z(z_value)
            )
            print("plot z)", z_value)
            self.last_z_value = z_value  # Update the last z value

        else:
            z_value = self.get_last_known_z()  # Use the last known z value
            x_scaled_for_z_canvas, y_scaled_for_z_canvas = (
                self.plot_z_value_on_canvas_z(z_value)
            )

        # If there's at least one point, and both current and last point have 'x' and 'y' arguments,
        # then draw a line from the last point to the current one using canvas coordinates
        if len(self.path_points) > 0:
            last_canvas_x, last_canvas_y = self.path_points[-1]["canvas_coordinates"]
            self.canvas.create_line(
                last_canvas_x,
                last_canvas_y,
                x_for_canvas,
                y_for_canvas,
                fill="black",
                tags=f"line{len(self.path_points)}",
            )

        self.point_counter += 1

        # Draw shape for command on XY canvas
        # Based on command type, create a different shape
        self.create_shape_on_canvas(command, x_for_canvas, y_for_canvas)

        self.path_points.append(
            {
                "type": command,
                "arguments": arguments,
                "canvas_coordinates": (x_for_canvas, y_for_canvas),
                "canvas_z_coordinates": (x_scaled_for_z_canvas, y_scaled_for_z_canvas),
            }
        )
        return 0

    """This event handler is triggered when the user clicks on the XY plane canvas.
    It allows the user to specify the type and details of a command at the
    clicked location, plotting this command on the canvas and 
    updating the Z axis canvas if necessary."""

    def on_canvas_click(self, event):
        try:
            canvas_x, canvas_y = event.x, event.y

            # Command type dropdown selection
            command = self.get_command_type()
            if not command:  # User closed the dialog or pressed cancel
                return

            # Get arguments for the specific command
            arguments = self.get_command_arguments(command)
            if not arguments:  # User closed the dialog or pressed cancel
                return

            if command in ["SCHEDULE_FLY_TO_Z", "SCHEDULE_MOVE_XYZ"]:
                z_value = arguments.get("z", 0)
                x_scaled, y_scaled = self.plot_z_value_on_canvas_z(z_value)
                print("plot z)", z_value)
                self.last_z_value = z_value  # Update the last z value

            else:
                z_value = self.get_last_known_z()  # Use the last known z value
                x_scaled, y_scaled = self.plot_z_value_on_canvas_z(z_value)

            # If there's at least one point, and both current and last point have 'x' and 'y' arguments,
            # then draw a line from the last point to the current one using canvas coordinates
            if len(self.path_points) > 0:
                last_canvas_x, last_canvas_y = self.path_points[-1][
                    "canvas_coordinates"
                ]
                self.canvas.create_line(
                    last_canvas_x,
                    last_canvas_y,
                    canvas_x,
                    canvas_y,
                    fill="black",
                    tags=f"line{len(self.path_points)}",
                )

            # Based on command type, create a different shape
            self.create_shape_on_canvas(
                command, canvas_x, canvas_y
            )  # used to draw shapes on canvas

            self.canvas.create_text(
                canvas_x,
                canvas_y - 10,
                text=str(len(self.path_points) + 1),
                tags=f"text{len(self.path_points)}",
            )

            self.path_points.append(
                {
                    "type": command,
                    "arguments": arguments,
                    "canvas_coordinates": (canvas_x, canvas_y),
                    "canvas_z_coordinates": (x_scaled, y_scaled),
                }
            )

        except Exception as e:
            print("Error:", e)

    def get_last_known_z(self):
        """
        Retrieves the Z value (altitude) of the most recently added point that includes a Z value.
        This is used when plotting new points or commands that do not explicitly include a Z value,
        allowing the application to maintain continuity in the flight path's altitude by defaulting
        to the last known altitude.
        """
        for point in reversed(self.path_points):
            z_value = point["arguments"].get("z")
            if z_value is not None:
                return z_value
        return 0  # default if no Z-value was ever

    def redraw_canvas_z(self):
        """
        Clears and redraws all points on the Z axis canvas based on the current list of path points.
        This method is called after significant changes to the path (e.g., adding many points, deleting points)
        to ensure the Z axis canvas accurately reflects the current flight path, adjusting the scaling
        of the canvas if necessary to accommodate the number of points.
        """

        for idx, point in enumerate(self.path_points, start=1):
            x_scaled = (400 / self.expected_total_points) * idx
            z = point["arguments"].get("z", 0)
            max_z_value = 20
            y_scaled = 200 - (z / max_z_value) * 200

            self.canvas_z.create_oval(
                x_scaled - 2, y_scaled - 2, x_scaled + 2, y_scaled + 2, fill="red"
            )
            self.canvas_z.create_text(x_scaled, y_scaled - 10, text=str(idx))

            if idx > 1:  # If there's a previous point, draw a line to it
                last_x_scaled, last_y_scaled = (400 / self.expected_total_points) * (
                    idx - 1
                ), 200 - (
                    self.path_points[idx - 2]["arguments"].get("z", 0) / max_z_value
                ) * 200
                self.canvas_z.create_line(
                    last_x_scaled, last_y_scaled, x_scaled, y_scaled
                )

    """Plots the Z value (altitude) on the Z axis canvas, 
    adjusting the scale if the number of points exceeds the initial expected total.
    Returns the scaled X and Y coordinates of the point on the Z axis canvas."""

    def plot_z_value_on_canvas_z(self, z=None):
        if z is None and self.path_points:
            z = self.path_points[-1]["arguments"].get("z", 0)
        #    # Handle points without explicit Z value
        #     if z is None and hasattr(self, "prev_z"):
        #         z = self.prev_z
        #     elif z is not None:
        #         self.prev_z = z
        #     else:  # This handles the case where it's the first point and doesn't have a Z value
        #         return

        # I'm assuming the same scaling from the previous code example, adjust if necessary
        # Adjusting X scaling
        # Check if we've exceeded the current expected total points
        if self.point_counter > self.expected_total_points:
            self.expected_total_points *= 2
            self.canvas_z.delete("all")  # Clear canvas
            self.redraw_canvas_z()  # Redraw all points based on new scale

        x_scaled = (400 / self.expected_total_points) * self.point_counter

        max_z_value = 20  # Adjust this according to your data's range
        y_scaled = 200 - (z / max_z_value) * 200

        self.canvas_z.create_oval(
            x_scaled - 2, y_scaled - 2, x_scaled + 2, y_scaled + 2, fill="red"
        )
        self.canvas_z.create_text(x_scaled, y_scaled - 10, text=str(self.point_counter))

        if self.path_points:  # If there's a previous point, draw a line to it
            last_x_scaled, last_y_scaled = self.path_points[-1]["canvas_z_coordinates"]
            self.canvas_z.create_line(last_x_scaled, last_y_scaled, x_scaled, y_scaled)

        return x_scaled, y_scaled  # Ensure you return these values

    def draw_axis_names(self):
        """
        Draws axis labels on the Z axis canvas to improve readability and understanding of the graph.
        It labels the horizontal axis as 'Point Number' to indicate the sequence of points,
        and the vertical axis as 'Height' to represent the Z values (altitude) associated with each point.
        """
        self.canvas_z.create_text(200, 190, text="Point Number", anchor="s")
        self.canvas_z.create_text(5, 100, text="Height", anchor="w", angle=90)

    """
    These methods are used for visual feedback in the UI, such as 
    drawing shapes that represent commands on the canvas, 
    labeling axes, and updating labels after deleting points.
    """

    def create_shape_on_canvas(self, command, x, y):
        size = 5  # General size
        if command == "SCHEDULE_MOVE_XYZ":
            self.canvas.create_oval(
                x - size,
                y - size,
                x + size,
                y + size,
                fill="black",
                tags=f"point{len(self.path_points)}",
            )
        elif command == "SCHEDULE_FLY_TO_Z":
            self.canvas.create_line(
                x,
                y - size,
                x,
                y + size,
                fill="black",
                tags=f"point{len(self.path_points)}",
            )  # Arrow pointing up
        elif command == "SCHEDULE_FLY_TO_YAW":
            self.canvas.create_oval(
                x - size,
                y - size,
                x + size,
                y + size,
                fill="white",
                outline="black",
                tags=f"point{len(self.path_points)}",
            )  # Ring
        elif command == "SCHEDULE_WAIT_FOR_PERIOD":
            offset = 3
            self.canvas.create_line(
                x - offset,
                y - offset,
                x + offset,
                y + offset,
                fill="black",
                tags=f"point{len(self.path_points)}",
            )  # Small X
            self.canvas.create_line(
                x + offset,
                y - offset,
                x - offset,
                y + offset,
                fill="black",
                tags=f"point{len(self.path_points)}",
            )  # Small X
        elif command == "SCHEDULE_SET_XY_SPEED":
            # Triangle pointing to side
            self.canvas.create_polygon(
                x + size,
                y,
                x - size,
                y + size,
                x - size,
                y - size,
                fill="black",
                tags=f"point{len(self.path_points)}",
            )
        else:
            self.canvas.create_oval(
                x - 5,
                y - 5,
                x + 5,
                y + 5,
                fill="black",
                tags=f"point{len(self.path_points)}",
            )

    """
    get_command_type and get_command_arguments: 
    These methods display dialogs to the user for selecting a command type and 
    entering the necessary arguments for the selected command.
    """

    def get_command_type(self):
        dialog = CommandDialog(self)
        self.wait_window(dialog.top)
        return dialog.result

    def get_action_type(self):
        action = ActionDialog(self)
        self.wait_window(action.top)
        return action.result

    def get_command_arguments(self, command):
        if command == "SCHEDULE_MOVE_XYZ":
            action = self.get_action_type()
            delay = simpledialog.askfloat("Arguments", "Enter delay:")
            velocity = simpledialog.askfloat("Arguments", "Enter velocity:")
            x = simpledialog.askfloat("Arguments", "Enter x coordinate:")
            y = simpledialog.askfloat("Arguments", "Enter y coordinate:")
            yaw = simpledialog.askfloat("Arguments", "Enter yaw:")
            z = simpledialog.askfloat("Arguments", "Enter z:")
            return {
                "x": x,
                "y": y,
                "action": action,  # Added this line
                "velocity": velocity,
                "yaw": yaw,
                "z": z,
                "delay": delay,
            }
        # Add other command types and their specific argument prompts here
        # For the sake of space, I will just add one more. Add others similarly.
        elif command == "SCHEDULE_FLY_TO_XY":
            x = simpledialog.askfloat("Arguments", "Enter x:")
            y = simpledialog.askfloat("Arguments", "Enter y:")
            return {"x": x, "y": y}

        elif command == "SCHEDULE_FLY_TO_Z":
            z = simpledialog.askfloat("Arguments", "Enter z:")
            return {"z": z}
        elif command == "SCHEDULE_FLY_TO_YAW":
            yaw = simpledialog.askfloat("Arguments", "Enter yaw:")
            return {"yaw": yaw}
        elif command == "SCHEDULE_SET_XY_SPEED":
            speed = simpledialog.askfloat("Arguments", "Enter speed:")
            return {"speed": speed}
        elif command == "SCHEDULE_SET_PAYLOAD_RECORDING":
            return {}
        elif command == "SCHEDULE_WAIT_FOR_PERIOD":
            period = simpledialog.askfloat("Arguments", "Enter period :")
            return {"period": period}
        elif command == "SCHEDULE_TAKE_PICTURE":
            return {}
        elif command == "SCHEDULE_RETURN_TO_TAKEOFF_POSITION":
            x = 0.0
            y = 0.0
            return {"x": x, "y": y}
        else:
            return None

        # Parsing function to get all the FLY_TO commands

    def delete_point(self, event):
        """
        Deletes a point from the XY plane canvas when a user clicks close to it. This method identifies
        the clicked point, removes it from the list of path points, and then updates the canvas by
        removing the point's graphical representation and adjusting the labels of remaining points to
        reflect the new order.
        """
        x, y = event.x, event.y
        items = self.canvas.find_overlapping(x - 5, y - 5, x + 5, y + 5)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if "point" in tag:
                    idx = int(tag[5:])
                    self.path_points.pop(idx)
                    self.canvas.delete(f"point{idx}", f"text{idx}")
                    self.refresh_numbers()

    def refresh_numbers(self):
        """
        Updates the labels for each point on the XY plane canvas after a point has been deleted.
        This ensures that the sequence numbers displayed next to each point are always correct,
        reflecting their current order in the path following any modifications.
        """
        for i, point in enumerate(self.path_points):
            self.canvas.itemconfig(f"text{i}", text=str(i + 1))

    """    
    export_to_json: Converts the plotted points and commands into a structured JSON
    format suitable for the drone to interpret. 
    This method includes checks to ensure the path is valid and then 
    prompts the user to save the file.
    """

    def export_to_json(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )

        # Check for at least one SCHEDULE_MOVE_XYZ or SCHEDULE_FLY_TO_XY command
        if not any(
            point["type"] in ["SCHEDULE_MOVE_XYZ", "SCHEDULE_FLY_TO_XY"]
            for point in self.path_points
        ):
            messagebox.showerror(
                "Error",
                "At least one SCHEDULE_MOVE_XYZ or SCHEDULE_FLY_TO_XY command is required before exporting.",
            )
            return
        if file:  # If user didn't cancel the save dialog
            initial_block = [
                {"arguments": {"version": "2.0.0"}, "type": "SCHEDULE_PLANNER_VERSION"},
                {"arguments": {"speed": 1.5}, "type": "SCHEDULE_SET_XY_SPEED"},
                {"arguments": {"yaw": 90}, "type": "SCHEDULE_FLY_TO_YAW"},
            ]

            final_block = [
                {"type": "SCHEDULE_RETURN_TO_TAKEOFF_POSITION"},
                {
                    "type": "START_TASK",
                    "arguments": {
                        "task": {
                            "description": "",
                            "id": "JsNis48JmatqrH8id68b",
                            "name": "42L C-G",
                        }
                    },
                },
            ]

        # Define a custom order for the arguments
        arguments_order = [
            "action",
            "delay",
            "velocity",
            "x",
            "y",
            "yaw",
            "z",
            "speed",
            "period",
        ]

        # Create a copy of path_points excluding the canvas_coordinates and with ordered arguments
        export_points = []
        for point in self.path_points:
            ordered_arguments = {
                k: point["arguments"][k]
                for k in arguments_order
                if k in point["arguments"]
            }
            export_point = {"arguments": ordered_arguments, "type": point["type"]}
            export_points.append(export_point)

        with open(file, "w") as f:
            json.dump(initial_block + export_points + final_block, f)
        messagebox.showinfo("Success", "Commands exported successfully!")

        # After saving the JSON file
        self.send_via_ssh(file)

    """
    send_via_ssh: Handles the transfer of the exported JSON file to the drone via SSH,
    using the Paramiko library for the SSH connection.
    """

    def send_via_ssh(self, filepath):
        ssh_dialog = SSHDialog(self)
        self.wait_window(ssh_dialog.top)
        username, ip_address = (
            ssh_dialog.result.split("@") if ssh_dialog.result else (None, None)
        )

        if not username or not ip_address:
            return

        password = simpledialog.askstring(
            "SSH Authentication", "Enter password for SSH:", show="*"
        )

        try:
            transport = paramiko.Transport((ip_address, 22))
            transport.connect(username=username, password=password)

            sftp = paramiko.SFTPClient.from_transport(transport)
            # Extract the filename without extension for the directory name
            filename = filepath.split("/")[-1]
            base_filename = filename.rsplit(".", 1)[0]

            # Create directory under /home/root/paths
            remote_dir_path = f"/home/root/paths/{base_filename}"
            try:
                sftp.mkdir(remote_dir_path)
            except IOError:
                # Directory probably already exists; you can either pass or handle this differently
                pass

            # Upload the file to the newly created directory
            remote_file_path = f"{remote_dir_path}/{filename}"
            sftp.put(filepath, remote_file_path)

            sftp.close()
            transport.close()

            messagebox.showinfo(
                "Success", f"File successfully sent to {username}@{ip_address}!"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send file due to: {str(e)}")


"""custom dialog windows for entering SSH connection details
and command type selection"""


class SSHDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("SSH Destination")

        tk.Label(self.top, text="Enter destination (username@IP_ADDRESS)").pack(pady=10)

        self.entry = tk.Entry(self.top)
        self.entry.pack(pady=10)
        # Set the default value for the entry widget
        self.entry.insert(0, "root@192.168.0.227")

        self.btn_ok = tk.Button(self.top, text="OK", command=self.on_ok)
        self.btn_ok.pack(pady=10)

        self.result = None

    def on_ok(self):
        self.result = self.entry.get()
        self.top.destroy()


class CommandDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Command Type Selection")

        tk.Label(self.top, text="Select Command Type").pack(pady=10)

        self.command_types = [
            "SCHEDULE_MOVE_XYZ",
            "SCHEDULE_FLY_TO_XY",
            "SCHEDULE_FLY_TO_Z",
            "SCHEDULE_FLY_TO_YAW",
            "SCHEDULE_SET_XY_SPEED",
            "SCHEDULE_SET_PAYLOAD_RECORDING",
            "SCHEDULE_WAIT_FOR_PERIOD",
            "SCHEDULE_TAKE_PICTURE",
            "SCHEDULE_RETURN_TO_TAKEOFF_POSITION",
        ]

        self.combobox = ttk.Combobox(self.top, values=self.command_types)
        self.combobox.current(0)
        self.combobox.pack(pady=10)

        self.btn_ok = tk.Button(self.top, text="OK", command=self.on_ok)
        self.btn_ok.pack(pady=10)

        self.result = None

    def on_ok(self):
        self.result = self.combobox.get()
        self.top.destroy()


class ActionDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Action Type Selection")

        tk.Label(self.top, text="Select Action Type").pack(pady=10)

        self.action_types = [
            "NO_ACTION",
            "STOP_BURST",
            "START_BURST",
        ]

        self.combobox = ttk.Combobox(self.top, values=self.action_types)
        self.combobox.current(0)
        self.combobox.pack(pady=10)

        self.btn_ok = tk.Button(self.top, text="OK", command=self.on_ok)
        self.btn_ok.pack(pady=10)

        self.result = None

    def on_ok(self):
        self.result = self.combobox.get()
        self.top.destroy()


app = FlightPlannerApp()
app.mainloop()
