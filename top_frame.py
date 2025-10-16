import customtkinter as ctk


class TopFrame(ctk.CTkFrame):
    def __init__(self, master, theme):
        super().__init__(master)
        self.theme = theme

        # Let TopFrame fill width only (no unnecessary vertical padding)
        self.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))

        # Make the TopFrame expand horizontally
        master.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Title label
        self.title_lbl = ctk.CTkLabel(
            self, text="Project Todo Manager", font=("Arial", 16, "bold")
        )
        self.title_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        # Switch for theme toggle
        self.switch_var = ctk.StringVar(value=self.theme)

        self.my_switch = ctk.CTkSwitch(
            self,
            text=self.switch_var.get(),
            command=self.switching,
            variable=self.switch_var,
            onvalue="light",
            offvalue="dark"
        )
        self.my_switch.grid(row=0, column=1, sticky="e", padx=10, pady=10)

    def switching(self):
        """ A method that is used to change theme with toggling """
        # We change the theme and also the text of Switch to the current theme name

        current_value = self.switch_var.get()

        if current_value == "dark":
            ctk.set_appearance_mode("dark")
            self.my_switch.configure(text="dark")

        else:
            ctk.set_appearance_mode("light")
            self.my_switch.configure(text="light")
