import customtkinter as ctk

import pystray
from pystray import Icon, MenuItem, Menu

from PIL import Image, ImageDraw

import sys
import os
import time
import threading

from monitor_utils import get_monitors_info, set_refresh_rate, set_refresh_rate_br, set_brightness, set_resolution
from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool, reg_write_list, reg_read_list, reg_write_dict, reg_read_dict

import ctypes
from ctypes import wintypes
import win32api, win32con

import screen_brightness_control as sbc

import config
import winreg


# MARK: MonitorTuneApp
class MonitorTuneApp:
    def __init__(self, icon_path, settings_icon):
        print("MonitorTuneApp init ------------------------------------------------")

        self.icon_path = icon_path
        self.settings_icon = settings_icon
        

        self.window_width = 357
        self.window_height = 231

        self.taskbar_height = 48
        self.edge_padding = 11
        # self.edge_padding = 0

        self.border_color_light = "#bebebe"
        self.border_color_dark = "#404040"

        self.bg_color_light = "#f3f3f3"
        self.bg_color_dark = "#202020"

        self.fr_color_light = "#fbfbfb"
        self.fr_color_dark = "#2b2b2b"

        
        self.root = ctk.CTk()

        self.main_scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        print(f"Scale factor: {self.main_scale_factor}")

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        print(f"Screen res: {self.screen_width} x {self.screen_height}")

        self.settings_window = None

        self.window_open = False
        self.brightness_sync_thread = None


        self.brightness_values = {}
        self.load_brightness_values_from_registry()


        self.excluded_rates = list(map(int, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates")))

        self.monitors_order = reg_read_list(config.REGISTRY_PATH, "MonitorsOrder")


        self.show_res_combobox = reg_read_bool(config.REGISTRY_PATH, "ShowResCombobox")
        self.enable_res_combobox = reg_read_bool(config.REGISTRY_PATH, "EnableResCombobox")

        self.restore_last_brightness = reg_read_bool(config.REGISTRY_PATH, "RestoreLastBrightness")
        

        # self.show_refresh_rates = read_show_refresh_rates_from_registry()  # Add a flag to control the display of refresh rates
        self.show_refresh_rates = reg_read_bool(config.REGISTRY_PATH, "ShowRefreshRates")
        # print(f"show_refresh_rates {self.show_refresh_rates}")
        self.setup_window()


        # self.root.bind("<Configure>", self.on_configure)


    # def on_configure(self, event):
    #     print("on_configure", event)


    # MARK: setup_window()
    def setup_window(self):
        print("setup_window ------------------------------------------------")
        self.root.bind("<FocusOut>", self.on_focus_out)
        self.root.withdraw()

        # self.x_position = self.screen_width  - self.window_width  - self.edge_padding
        # self.y_position = self.screen_height - self.window_height - self.edge_padding - self.taskbar_height
        self.x_position = int((self.screen_width - self.window_width - self.edge_padding) * self.main_scale_factor)
        self.y_position = int((self.screen_height - self.window_height - self.edge_padding - self.taskbar_height) * self.main_scale_factor)
        print("window height", self.window_height)  
        print(f"x_position {self.x_position} y_position {self.y_position}")

        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")

        self.root.config(background="#000001")
        self.root.attributes("-transparentcolor", "#000001")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        # self.root.configure(fg_color="green")

        self.root.overrideredirect(True)  # Removes the default window decorations
        self.root.attributes('-topmost', 'True')

        self.window_frame = ctk.CTkFrame(self.root, 
                                         corner_radius=9, 
                                         width=400, 
                                         bg_color="#000001", 
                                         fg_color=(self.bg_color_light, self.bg_color_dark),
                                         border_color=(self.border_color_light, self.border_color_dark), 
                                         border_width=1)
        self.window_frame.grid(sticky="nsew")
        self.window_frame.grid_columnconfigure(0, weight=1)
        self.window_frame.grid_rowconfigure(0, weight=1)


        self.main_frame = ctk.CTkFrame(self.window_frame, 
                                       corner_radius=6, 
                                       fg_color=(self.bg_color_light, self.bg_color_dark))
        # self.main_frame.configure(fg_color="red")
        self.main_frame.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)


        # profiles_frame = ctk.CTkFrame(self.window_frame, corner_radius=6, fg_color=self.fr_color_dark)
        # profiles_frame.configure(fg_color="red")
        # profiles_frame.grid(row=1, column=0, padx=(5, 5), pady=(0, 5), sticky="ew")
        # # profiles_frame.columnconfigure(0, weight=1)

        # p_button = ctk.CTkButton(profiles_frame, text="Profiles", width=1)
        # p_button.configure(border_width=1, border_color="gray", fg_color=self.fr_color_dark)
        # p_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        # profiles_frame.update()
        # pf_height = profiles_frame.winfo_height()
        # print(f"pf_height {pf_height}")


        self.bottom_frame = ctk.CTkFrame(self.window_frame, height=48, corner_radius=6, fg_color=(self.bg_color_light, self.bg_color_dark))
        # bottom_frame.configure(fg_color="red")
        self.bottom_frame.grid(row=2, column=0, padx=(5, 5), pady=(0, 5), sticky="ew")
        # bottom_frame.grid(row=2, column=0, padx=(7, 7), pady=(0, 7), sticky="ew")
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.bind("<MouseWheel>", self.on_bottom_frame_scroll)

        name_title = ctk.CTkLabel(self.bottom_frame, 
                                  text="Scroll to adjust monitors", 
                                  font=("Segoe UI", 14),
                                  height=28)#, "bold"))
        # name_title.configure(bg_color="blue")
        name_title.grid(row=0, column=0, padx=(9, 0), pady=(9, 11), sticky="w")
        name_title.bind("<MouseWheel>", self.on_bottom_frame_scroll)

        icon = Image.open(self.settings_icon)
        settings_button = ctk.CTkButton(self.bottom_frame, 
                                        text="", 
                                        image=ctk.CTkImage(icon), 
                                        width=35,
                                        height=35, 
                                        command=self.open_settings_window)
        settings_button.grid(row=0, column=1, padx=(0, 7), pady=(0, 0), sticky="e")


        # self.root.update() #////////////////////////////////////////////////
        # self.load_ui()
        # self.root.after(0, self.load_ui) #////////////////////////////////////////////////
        self.on_tray_click()






    # MARK: load_ui()
    def load_ui(self):
        print("load_ui ------------------------------------------------")
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        monitors_info = get_monitors_info()
        # print(f"monitors_info {monitors_info}")
        # monitors_info.reverse()  # Invert the order of monitors

        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitors_order = [serial for serial in self.monitors_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]

        # new_window_height = 65 - 5 + 5
        new_window_height = 48 + 5 # bottom_frame height + padding
        # new_window_height += 5
        new_window_height += 1
        new_window_height += 3

        # if self.main_scale_factor == 1.0:
        #     # new_window_height += 1
        #     # print("+1.0")
        # elif self.main_scale_factor == 1.25: 
        #     # for _ in range(len(monitors_info)):
        #     new_window_height += 4 * len(monitors_info)
        #     # new_window_height += int(    ((15 * len(monitors_info)) * self.main_scale_factor)  - (15 * len(monitors_info))        )
        #     # print(f"+1.25 -------------------- {int(    ((15 * len(monitors_info)) * self.main_scale_factor)  - (15 * len(monitors_info))        )}")
        # elif self.main_scale_factor == 1.5:
        #     new_window_height += 5
        #     print("+1.5")

        for index_2, _ in enumerate(range(1)):
            for index, monitor_serial in enumerate(monitors_order):

                monitor = monitors_dict[monitor_serial]

                monitor_frame = ctk.CTkFrame(self.main_frame, 
                                            corner_radius=6, 
                                            fg_color=(self.fr_color_light, self.fr_color_dark))
                # monitor_frame.configure(fg_color="green")
                # monitor_frame.grid(row=index, column=0, padx=(2, 2), pady=(2, 5), sticky="ew")
                monitor_frame.grid(row=index+index_2*10, column=0, padx=(2, 2), pady=(2, 5), sticky="ew")
                monitor_frame.columnconfigure(0, weight=1)

                new_window_height += 7 # monitor_frame pady
                # new_window_height += int(7 * self.main_scale_factor)
                
                label_frame = ctk.CTkFrame(monitor_frame, corner_radius=6)
                label_frame.configure(fg_color=(self.fr_color_light, self.fr_color_dark))
                # label_frame.configure(fg_color="blue")
                label_frame.grid(row=0, column=0, padx=(2, 2), pady=(2, 0), sticky="ew")
                label_frame.columnconfigure(1, weight=1)

                monitor_label = ctk.CTkLabel(label_frame, 
                                            text=monitor["display_name"], 
                                            font=("Segoe UI", 16, "bold"))
                # monitor_label.configure(bg_color="red")
                monitor_label.grid(row=0, column=0, padx=(10, 0), pady=(5, 5), sticky="w")


                if self.show_res_combobox:
                    if self.enable_res_combobox:
                        available_resolutions = monitor["AvailableResolutions"]
                        sorted_resolutions = sorted(available_resolutions, key=lambda res: res[0] * res[1], reverse=True)
                        formatted_resolutions = [f"{width}x{height}" for width, height in sorted_resolutions]

                        res_combobox = ctk.CTkOptionMenu(label_frame, 
                                                        values=formatted_resolutions, 
                                                        font=("Segoe UI", 14, "bold"))
                        # res_combobox.configure(bg_color="red")
                        res_combobox.set(monitor["Resolution"])
                        res_combobox.configure(command=lambda value, ms=monitor_serial, frame=label_frame: self.on_resolution_select(ms, value, frame))

                        res_combobox.grid(row=0, column=1, padx=(0, 5), pady=(5, 5), sticky="e")
                    else:
                        res_btn = ctk.CTkButton(label_frame, text=f"{monitor["Resolution"]}", width=110, hover=False, font=("Segoe UI", 14, "bold"))
                        # res_btn.configure(border_width=1, border_color="gray", fg_color=self.btn_bg_color)
                        res_btn.grid(row=0, column=1, padx=(0, 5), pady=(5, 5), sticky="e")

                        # res_combobox.configure(state="disabled")


                if self.show_refresh_rates:
                    refresh_rates = monitor["AvailableRefreshRates"]
                    refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates]

                    if len(refresh_rates) >= 2:
                        rr_frame = ctk.CTkFrame(monitor_frame, corner_radius=6)
                        rr_frame.configure(fg_color=(self.fr_color_light, self.fr_color_dark))
                        # rr_frame.configure(fg_color="red")
                        rr_frame.grid(row=1, column=0, padx=(5, 5), pady=(2, 2), sticky="ew")
                        self.update_refresh_rate_frame(monitor_serial, monitor, rr_frame)

                        rows = (len(refresh_rates) + 6 - 1) // 6
                        new_window_height += rows * 28 # rr_frame row
                        new_window_height += 4 # rr_frame pady


                br_frame = ctk.CTkFrame(monitor_frame, corner_radius=6, fg_color=(self.fr_color_light, self.fr_color_dark))
                # br_frame.configure(fg_color="yellow")
                br_frame.grid(row=2, column=0, padx=(2, 2), pady=(0, 2), sticky="ew")
                br_frame.columnconfigure(0, weight=1)
                br_frame.columnconfigure(1, weight=0)


                if self.restore_last_brightness and monitor['serial'] in self.brightness_values:
                    br_level = int(self.brightness_values[monitor['serial']]['brightness'])
                else:
                    br_level = sbc.get_brightness(display=monitor['serial'])[0]
                
                br_slider = ctk.CTkSlider(br_frame, from_=0, to=100, number_of_steps=100, height=20)
                # br_slider.set(sbc.get_brightness(display=monitor['serial'])[0])
                br_slider.set(br_level)   
                # br_slider.configure(bg_color="green")
                br_slider.grid(row=0, column=0, padx=(3, 0), pady=(2, 2), sticky="ew")

                br_label = ctk.CTkLabel(master=br_frame, 
                                        # text=int(br_slider.get()), 
                                        text=br_level, 
                                        corner_radius=6, 
                                        font=("Segoe UI", 22, "bold"), 
                                        anchor="n", 
                                        width=50, height=34)
                # br_label.configure(fg_color="blue")
                br_label.grid(row=0, column=1, padx=(0, 5), pady=(2, 2), sticky="nsew")

                br_slider.configure(command=lambda value, idx=monitor_serial, label=br_label: self.on_br_slider_change(idx, value, label))
                br_frame.bind("<MouseWheel>", command=lambda event, idx=monitor_serial, label=br_label, slider=br_slider: self.on_br_slider_scroll(event, slider, label, idx))
                br_slider.bind("<MouseWheel>", command=lambda event, idx=monitor_serial, label=br_label, slider=br_slider: self.on_br_slider_scroll(event, slider, label, idx))


                self.brightness_values[monitor['serial']] = {'brightness': br_level, 'slider': br_slider, 'label': br_label}
                # print(f"self.brightness_values {self.brightness_values}")


                # new_window_height += 84 # 38 * 2 + 4
                new_window_height += (38 * 2) + 2 + 2
                # new_window_height += (38 * 2) + 2 + 3


        print(f"new_window_height {new_window_height}")
        self.window_height = new_window_height

        self.update_sizes()
        # self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        

    # MARK: update_sizes()
    def update_sizes(self):
        print("update_sizes")

        self.main_scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        print(f"Scale factor: {self.main_scale_factor}")

        user32 = ctypes.windll.user32
        self.screen_width = int(user32.GetSystemMetrics(0) / self.main_scale_factor)
        self.screen_height = int(user32.GetSystemMetrics(1) / self.main_scale_factor)
        print(f"   Screen res: {self.screen_width} x {self.screen_height}")

        self.x_position = int((self.screen_width - self.window_width - self.edge_padding) * self.main_scale_factor)
        self.y_position = int((self.screen_height - self.window_height - self.edge_padding - self.taskbar_height) * self.main_scale_factor)
        print(f"   x_position {self.x_position} y_position {self.y_position}")


    # MARK: on_refresh_rate_btn()
    def on_refresh_rate_btn(self, monitor_serial, monitor, value, frame):
        print(f"on_refresh_rate_btn {monitor_serial} {value}")

        set_refresh_rate_br(monitor, value, refresh=False)

        monitors_info = get_monitors_info()
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

        fresh_monitor = monitors_dict[monitor_serial]
        self.update_refresh_rate_frame(monitor_serial, fresh_monitor, frame)
        # self.load_ui()



    # MARK: update_refresh_rate_frame()
    def update_refresh_rate_frame(self, monitor_serial, monitor, frame):
        print(f"update_refresh_rate_frame {monitor_serial}")

        for widget in frame.winfo_children():
            widget.destroy()

        refresh_rates = monitor["AvailableRefreshRates"]

        refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates]

        # num_columns = 6
        if len(refresh_rates) > 6:
            num_columns = 6
        else:
            num_columns = len(refresh_rates)
        
        for i in range(num_columns):
            frame.columnconfigure(i, weight=1)

        for r_index, rate in enumerate(refresh_rates):
            rr_button = ctk.CTkButton(frame, 
                                      text=f"{rate} Hz", 
                                      font=("Segoe UI", 12), 
                                      width=1, height=24)
            
            if rate == monitor["RefreshRate"]:
                rr_button.configure(hover=False)
                # rr_button.configure(state="disabled")
                pass
            else:
                rr_button.configure(border_width=1, border_color="gray", fg_color=("gray", self.fr_color_dark))
                rr_button.configure(command=lambda rate=rate, 
                                    m_s=monitor_serial, mon=monitor, 
                                    frame=frame: self.on_refresh_rate_btn(m_s, mon, rate, frame))

            rr_button.grid(row=r_index // num_columns, 
                           column=r_index % num_columns, 
                           padx=2, pady=2, sticky="ew")
        
        # print("update_refresh_rate_frame height", frame.winfo_height())



    # MARK: on_resolution_select()
    def on_resolution_select(self, monitor_serial, resolution, frame):
        print(f"on_resolution_select {monitor_serial} {resolution}")
        
        monitors_info = get_monitors_info()
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
        width, height = map(int, resolution.split('x'))
        set_resolution(monitors_dict[monitor_serial]["Device"], width, height)

        self.update_sizes()
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")


    # MARK: on_br_slider_change()
    def on_br_slider_change(self, monitor_serial, value, label):
        print(f"on_br_slider_change {monitor_serial} {value}")
        label.configure(text=f"{int(value)}")
        self.brightness_values[monitor_serial]['brightness'] = int(value)  # Ensure value is an integer
        self.save_brightness_values_to_registry()

    # MARK: on_br_slider_scroll()
    def on_br_slider_scroll(self, event, slider, label, monitor_serial):
        print(f"on_br_slider_scroll {monitor_serial} {event.delta}")
        new_value = max(0, min(100, slider.get() + (1 if event.delta > 0 else -1)))
        slider.set(new_value)
        label.configure(text=f"{int(new_value)}")
        self.brightness_values[monitor_serial]['brightness'] = int(new_value)
        self.save_brightness_values_to_registry()


    # MARK: on_bottom_frame_scroll()
    def on_bottom_frame_scroll(self, event):
        print("on_bottom_frame_scroll ", event.delta)
        for monitor_serial, monitor in self.brightness_values.items():
            brightness = monitor['brightness']
            slider = monitor['slider']
            label = monitor['label']

            new_value = max(0, min(100, slider.get() + (1 if event.delta > 0 else -1)))
            slider.set(new_value)
            label.configure(text=f"{int(new_value)}")
            self.brightness_values[monitor_serial]['brightness'] = new_value
        self.save_brightness_values_to_registry()



    # MARK: open_settings_window()
    def open_settings_window(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            print("open_settings_window")

            self.settings_window = ctk.CTkToplevel(self.root)
            self.settings_window.title(f"{config.app_name} Settings")

            self.settings_window.minsize(400, 350)
            
            self.settings_window.grid_rowconfigure(0, weight=1)
            self.settings_window.grid_columnconfigure(0, weight=1)

            settings_window_width = 550
            settings_window_height = 475
            self.settings_window.geometry(f"{settings_window_width}x{settings_window_height}")

            # self.settings_window.after(250, lambda: self.settings_window.iconbitmap('icons/icon_color_dev.ico'))
            # self.settings_window.after(250, lambda: self.settings_window.iconbitmap(self.title_bar_icon))
            self.settings_window.after(250, lambda: self.settings_window.iconbitmap(self.icon_path))


            tabview = ctk.CTkTabview(self.settings_window)
            tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")



            def toggle_setting(setting_name, reg_setting_name, var):
                setattr(self, setting_name, var.get())
                reg_write_bool(config.REGISTRY_PATH, reg_setting_name, getattr(self, setting_name))
                self.load_ui()

            def create_setting_switch(parent, setting_name, reg_setting_name, setting_label, row_num):
                var = ctk.BooleanVar(value=getattr(self, setting_name))
                switch = ctk.CTkSwitch(parent, 
                                        text=setting_label, 
                                        variable=var, 
                                        command=lambda: toggle_setting(setting_name, reg_setting_name, var))
                # switch.pack(pady=15, padx=15)
                switch.grid(row=row_num, column=0, padx=10, pady=10, sticky="w")
                return switch



            # Додаємо вкладки
            general_tab = tabview.add("General")

            resolution_tab = tabview.add("Resolution")
            resolution_tab_frame = ctk.CTkFrame(resolution_tab)
            resolution_tab_frame.configure(fg_color="gray")
            resolution_tab_frame.pack(pady=(5, 0), fill="y", expand=True)

            refresh_rate_tab = tabview.add("Refresh Rate")
            refresh_rate_tab_frame = ctk.CTkFrame(refresh_rate_tab)
            refresh_rate_tab_frame.configure(fg_color="gray")
            refresh_rate_tab_frame.pack(pady=(5, 0), fill="y", expand=True)

            brightness_tab = tabview.add("Brightness")
            brightness_tab_frame = ctk.CTkFrame(brightness_tab)
            brightness_tab_frame.configure(fg_color="gray")
            brightness_tab_frame.pack(pady=(5, 0), fill="y", expand=True)


            # time_tab = tabview.add("Time adjustment")
            # hotkeys_tab = tabview.add("Hotkeys")
            about_tab = tabview.add("About")


            # MARK: General Tab
            monitors_info = get_monitors_info()
            # Створюємо словник, де ключ — серійний номер
            monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
            # print(f"monitors_dict {monitors_dict}")

            reg_order = reg_read_list(config.REGISTRY_PATH, "MonitorsOrder")
            # Сортуємо список моніторів відповідно до порядку з реєстру
            monitors_order = [serial for serial in reg_order if serial in monitors_dict]
            # Додаємо монітори, яких немає в реєстрі, в кінець списку
            monitors_order += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitors_order]


            order_settings_label = ctk.CTkLabel(general_tab, text="Reorder Monitors")
            order_settings_label.pack(pady=(10, 5))

            order_frame = ctk.CTkFrame(general_tab)


            def create_monitor_list():
                # Видалити старі віджети
                for widget in order_frame.winfo_children():
                    widget.destroy()

                # Додати нові віджети
                for i, monitor in enumerate(monitors_order):
                    row_frame = ctk.CTkFrame(order_frame)
                    row_frame.pack(fill="x", pady=2)

                    label = ctk.CTkLabel(row_frame, text=f"{monitors_dict[monitor]["display_name"]}", width=150, anchor="w")
                    label.pack(side="left", padx=5)

                    up_btn = ctk.CTkButton(row_frame, text="⬆", width=30, command=lambda i=i: move_up(i))
                    up_btn.pack(side="right", padx=2)

                    down_btn = ctk.CTkButton(row_frame, text="⬇", width=30, command=lambda i=i: move_down(i))
                    down_btn.pack(side="right", padx=2)

                    # id = ctk.CTkLabel(row_frame, text=f"id: {monitor}", width=175, anchor="w")
                    # id.pack(side="right", padx=5)

            def move_up(index):
                if index > 0:
                    monitors_order[index], monitors_order[index - 1] = monitors_order[index - 1], monitors_order[index]
                    create_monitor_list()
                    save_order()

            def move_down(index):
                if index < len(monitors_order) - 1:
                    monitors_order[index], monitors_order[index + 1] = monitors_order[index + 1], monitors_order[index]
                    create_monitor_list()
                    save_order()

            def save_order():
                print("New monitor order:", monitors_order)
                reg_write_list(config.REGISTRY_PATH, "MonitorsOrder", monitors_order)
                self.monitors_order = monitors_order
                self.load_ui()

            create_monitor_list()
            order_frame.pack()


            # MARK: Resolution Tab
            create_setting_switch(resolution_tab_frame, "show_res_combobox", "ShowResCombobox", "Show Resolutions", 1)
            create_setting_switch(resolution_tab_frame, "enable_res_combobox", "EnableResCombobox", "Resolution Change Ability", 2)


            # MARK: Refresh Rates Tab
            create_setting_switch(refresh_rate_tab_frame, "show_refresh_rates", "ShowRefreshRates", "Show Refresh Rates", 1)


            exclude_rr_label = ctk.CTkLabel(refresh_rate_tab_frame, text="Exclude Refresh Rates")
            exclude_rr_label.grid(row=2, column=0, padx=10, pady=(10 ,0), sticky="we")

            all_rates = set()
            for monitor in monitors_info:
                all_rates.update(monitor['AvailableRefreshRates'])
            all_rates = sorted(all_rates)

            excluded_rates = list(map(int, reg_read_list(config.REGISTRY_PATH, "ExcludedHzRates")))

            refresh_rate_tab_frame.rowconfigure(3, weight=1)
            # Створення прокручуваного фрейму
            scroll_frame = ctk.CTkScrollableFrame(refresh_rate_tab_frame)
            scroll_frame.grid(row=3, column=0, padx=5, pady=(5 ,10), sticky="nsew")

            # Функція для оновлення списку excluded
            def update_excluded(rate, value):
                print(f"Rate: {rate}, Switch: {value}")
                if value == 1:  # Якщо перемикач увімкнений
                    if rate in excluded_rates:
                        excluded_rates.remove(rate)
                else:  # Якщо перемикач вимкнений
                    if rate not in excluded_rates:
                        excluded_rates.append(rate)

                reg_write_list(config.REGISTRY_PATH, "ExcludedHzRates", excluded_rates)

                self.excluded_rates = excluded_rates
                print(f"Updated excluded list: {excluded_rates}")  # Виведення оновленого списку
                self.load_ui()

            for rate in all_rates:
                switch = ctk.CTkSwitch(scroll_frame, text=f"{rate} Hz")
                switch.pack(anchor="w", pady=5)
                
                # Встановлення початкового стану
                if rate in excluded_rates:
                    switch.deselect()
                else:
                    switch.select()
                
                # Прив'язка функції до події перемикання
                switch.configure(command=lambda rate=rate, switch=switch: update_excluded(rate, switch.get()))


            # MARK: Brightness Tab
            create_setting_switch(brightness_tab_frame, "restore_last_brightness", "RestoreLastBrightness", "Restore Last Brightness", 1)


        else:
            self.settings_window.focus()



    # MARK: create_tray_icon()
    def create_tray_icon(self):
        print("create_tray_icon")

        icon_image = Image.open(self.icon_path)
        # icon_image = Image.new('RGB', (64, 64), color=(255, 255, 255))

        menu = Menu(
            MenuItem("Quick access", self.on_tray_click, default=True, visible=False),
            MenuItem("Refresh displays", self.load_ui),
            MenuItem("Settings", self.open_settings_window),
            pystray.Menu.SEPARATOR,
            MenuItem("Exit", self.quit_app)
        )

        self.icon = Icon(config.app_name, icon_image, f"{config.app_name} {config.version}", menu)
        self.icon.run()



    # MARK: on_tray_click()
    def on_tray_click(self):
        if not self.root.winfo_viewable():
            print("on_tray_click show")
            self.update_sizes()

            self.root.geometry(f"{self.window_width}x{self.window_height}+{int(self.screen_width * self.main_scale_factor)}+{self.y_position}")
            print(f"   {self.window_width}x{self.window_height}+{int(self.screen_width * self.main_scale_factor)}+{self.y_position}")

            # self.load_ui()
            self.root.after(0, self.load_ui)
            # self.show_window()
            self.root.after(0, self.show_window)
            
        else:
            print("on_tray_click hide !!!")
            self.hide_window()



    # MARK: show_window()
    def show_window(self):
        print("show_window ------------------------------------------------")
        # self.root.geometry(f"{self.window_width}x{self.window_height}+{int(self.screen_width * self.main_scale_factor)}+{self.y_position}")

        self.root.deiconify()
        self.root.focus_force()

        self.window_open = True
        if self.brightness_sync_thread is None or not self.brightness_sync_thread.is_alive():
            print("brightness_sync_thread.start()")
            self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
            self.brightness_sync_thread.start()

        self.animate_window_open()
        # self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")

    # MARK: hide_window()
    def hide_window(self):
        print("hide_window")

        # self.animate_window_close()
        self.root.withdraw()
        self.window_open = False



    # MARK: on_focus_out()
    def on_focus_out(self, event):
        print("on_focus_out")
        if self.root.winfo_viewable():
            print("on_focus_out hide")
            self.hide_window()


    # MARK: brightness_sync()
    def brightness_sync(self):
        while self.window_open:
            # print("brightness_sync")

            # start_time = time.time()  # Start time measurement

            brightness_values_copy = self.brightness_values.copy()
            for monitor_serial, monitor in brightness_values_copy.items():
                brightness = monitor['brightness']
                current_brightness = sbc.get_brightness(display=monitor_serial)[0]
                
                if current_brightness != brightness:
                    print(f"set_brightness {monitor_serial} {brightness}")
                    set_brightness(monitor_serial, brightness)

            # end_time = time.time()  # End time measurement
            # print(f"Brightness sync took {end_time - start_time:.4f} seconds")

            time.sleep(0.25)



    # MARK: animate_window_open()
    def animate_window_open(self, speed=20):
        print("animate_window_open")
        for i in range(int(self.screen_width * self.main_scale_factor), self.x_position, -speed):
        # for i in range(self.screen_width, self.x_position, -speed):
            self.root.geometry(f"{self.window_width}x{self.window_height}+{i}+{self.y_position}")
            self.root.update()
            time.sleep(0.003)
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")
    
    # MARK: animate_window_close()
    def animate_window_close(self, speed=20):
        current_x_position = self.root.winfo_x()
        for i in range(current_x_position, self.screen_width, speed):
            self.root.geometry(f"{self.window_width}x{self.window_height}+{i}+{self.y_position}")
            self.root.update()
            time.sleep(0.003)



    # MARK: save_brightness_values_to_registry()
    def save_brightness_values_to_registry(self):
        brightness_data = {monitor_serial: {'brightness': int(data['brightness'])} for monitor_serial, data in self.brightness_values.items()}  # Ensure value is an integer
        reg_write_dict(config.REGISTRY_PATH, "BrightnessValues", brightness_data)

    # MARK: load_brightness_values_from_registry()
    def load_brightness_values_from_registry(self):
        brightness_data = reg_read_dict(config.REGISTRY_PATH, "BrightnessValues")
        print(f"brightness_data {brightness_data}")
        for monitor_serial, data in brightness_data.items():
            self.brightness_values[monitor_serial] = {'brightness': data['brightness'], 'slider': None, 'label': None}
        print(f"self.brightness_values {self.brightness_values}")



    # MARK: run()
    def run(self):
        threading.Thread(target=self.create_tray_icon, daemon=True).start()
        self.root.mainloop()

    # MARK: quit_app()
    def quit_app(self, icon, item):
        self.icon.stop()
        self.root.quit()



# MARK: main
if __name__ == "__main__":

    

    if getattr(sys, 'frozen', False):
        # Якщо програма запущена як EXE, шлях до іконки відносно до виконуваного файлу
        icon_path_s = os.path.join(sys._MEIPASS, 'icon_color.ico')
        # if is_dark_theme():
        #     icon_path = os.path.join(sys._MEIPASS, 'icon_light.ico')
        # else:
        #     icon_path = os.path.join(sys._MEIPASS, 'icon_dark.ico')

        settings_icon = os.path.join(sys._MEIPASS, 'setting_white.png')

    else:
        # Якщо програма запущена з Python, використовуємо поточну директорію
        icon_path_s = 'src/assets/icons/icon_color_dev.ico'
        # if is_dark_theme():
        #     icon_path = 'icons/icon_light.ico' 
        # else:
        #     icon_path = 'icons/icon_dark.ico'

        settings_icon = 'src/assets/icons/setting_white.png'



    app = MonitorTuneApp(icon_path_s, settings_icon)
    app.run()
