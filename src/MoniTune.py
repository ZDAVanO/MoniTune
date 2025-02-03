import customtkinter as ctk

import pystray
from pystray import Icon, MenuItem, Menu

from PIL import Image, ImageDraw

import sys
import os
import time
import threading

from monitor_utils import get_monitors_info, set_refresh_rate, set_refresh_rate_br, set_brightness, set_resolution
from reg_utils import is_dark_theme, key_exists, create_reg_key, reg_write_bool, reg_read_bool

import ctypes
from ctypes import wintypes
import win32api, win32con

import screen_brightness_control as sbc


import config
import winreg








# MARK: write_excluded_rates_to_registry()
def write_excluded_rates_to_registry(excluded_rates):
    try:
        excluded_rates_str = ",".join(map(str, excluded_rates))

        if not key_exists(config.REGISTRY_PATH):
            create_reg_key(config.REGISTRY_PATH)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, config.REGISTRY_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "ExcludedHzRates", 0, winreg.REG_SZ, excluded_rates_str)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error writing to registry: {e}")

# MARK: read_excluded_rates_from_registry()
def read_excluded_rates_from_registry():
    try:
        if not key_exists(config.REGISTRY_PATH):
            create_reg_key(config.REGISTRY_PATH)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, config.REGISTRY_PATH, 0, winreg.KEY_READ)
        
        try:
            value, _ = winreg.QueryValueEx(key, "ExcludedHzRates")
            excluded_rates = list(map(int, value.split(",")))
        except FileNotFoundError:
            excluded_rates = []

        winreg.CloseKey(key)

        # print(f"read_excluded_rates_from_registry(): {excluded_rates}")
        return excluded_rates
    
    except Exception as e:
        print(f"Error reading from registry: {e}")
        return []















# MARK: write_excluded_rates_to_registry()
def write_order_to_registry(order):
    print(f"write_order_to_registry {order}")
    try:
        order_str = ",".join(map(str, order))

        if not key_exists(config.REGISTRY_PATH):
            create_reg_key(config.REGISTRY_PATH)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, config.REGISTRY_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Order", 0, winreg.REG_SZ, order_str)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error writing to registry: {e}")

# MARK: read_excluded_rates_from_registry()
def read_order_from_registry():
    try:
        if not key_exists(config.REGISTRY_PATH):
            create_reg_key(config.REGISTRY_PATH)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, config.REGISTRY_PATH, 0, winreg.KEY_READ)
        
        try:
            value, _ = winreg.QueryValueEx(key, "Order")
            order = value.split(",")
        except FileNotFoundError:
            order = []

        winreg.CloseKey(key)

        return order
    
    except Exception as e:
        print(f"Error reading from registry: {e}")
        return []













# MARK: WRRS
class MonitorTuneApp:
    def __init__(self, icon_path):

        self.icon_path = icon_path

        self.window_width = 357
        self.window_height = 231

        self.taskbar_height = 48
        self.edge_padding = 11
        # self.edge_padding = 0

        self.border_dark_color = "#404040"
        self.bg_dark_color = "#202020"
        self.fr_dark_color = "#2b2b2b"

        self.border_light_color = "#bebebe"
        self.bg_light_color = "#f3f3f3"
        self.fr_light_color = "#fbfbfb"

        
        
        if is_dark_theme():
            ctk.set_appearance_mode("dark")
            self.bg_color = self.bg_dark_color
            self.border_color = self.border_dark_color
            self.fr_color = self.fr_dark_color
        else:
            ctk.set_appearance_mode("light")
            self.bg_color = self.bg_light_color
            self.border_color = self.border_light_color
            self.fr_color = self.fr_light_color


        # self.title_bar_icon = os.path.join(sys._MEIPASS, 'icon_color.ico')




        self.root = ctk.CTk()

        # self.root.iconbitmap('icons/icon_color_dev.ico')

        self.main_scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        print(f"Scale factor: {self.main_scale_factor}")

        self.screen_width = self.root.winfo_screenwidth()
        print(f"Screen width: {self.screen_width}")
        self.screen_height = self.root.winfo_screenheight()
        print(f"Screen height: {self.screen_height}")

        self.settings_window = None

        self.window_open = False
        self.brightness_sync_thread = None

        self.brightness_values = {}

        # self.prev_monitors_info = None

        self.excluded_rates = read_excluded_rates_from_registry()
        self.monitors_order = read_order_from_registry()


        # self.show_refresh_rates = read_show_refresh_rates_from_registry()  # Add a flag to control the display of refresh rates
        self.show_refresh_rates = reg_read_bool(config.REGISTRY_PATH, "ShowRefreshRates")
        self.setup_window()


    # MARK: setup_window()
    def setup_window(self):
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

        self.window_frame = ctk.CTkFrame(self.root, 
                                         corner_radius=9, 
                                         width=400, 
                                         bg_color="#000001", 
                                         border_color=self.border_color, 
                                         border_width=1)
        self.window_frame.grid(sticky="nsew")

        self.window_frame.grid_columnconfigure(0, weight=1)
        self.window_frame.grid_rowconfigure(0, weight=1)

        
        self.window_frame.configure(fg_color=self.bg_color)

        self.root.overrideredirect(True)  # Removes the default window decorations
        self.root.attributes('-topmost', 'True')

        self.main_frame = ctk.CTkFrame(self.window_frame, 
                                       corner_radius=6, 
                                       fg_color=self.bg_color)
        # self.main_frame.configure(fg_color="red")
        self.main_frame.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)






        # profiles_frame = ctk.CTkFrame(self.window_frame, corner_radius=6, fg_color=self.fr_dark_color)
        # profiles_frame.configure(fg_color="red")
        # profiles_frame.grid(row=1, column=0, padx=(5, 5), pady=(0, 5), sticky="ew")
        # # profiles_frame.columnconfigure(0, weight=1)

        # p_button = ctk.CTkButton(profiles_frame, text="Profiles", width=1)
        # p_button.configure(border_width=1, border_color="gray", fg_color=self.fr_dark_color)
        # p_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        # profiles_frame.update()
        # pf_height = profiles_frame.winfo_height()
        # print(f"pf_height {pf_height}")





        bottom_frame = ctk.CTkFrame(self.window_frame, height=48, corner_radius=6, fg_color=self.bg_color)
        # bottom_frame.configure(fg_color="red")
        bottom_frame.grid(row=2, column=0, padx=(5, 5), pady=(0, 5), sticky="ew")
        # bottom_frame.grid(row=2, column=0, padx=(7, 7), pady=(0, 7), sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.bind("<MouseWheel>", self.on_bottom_frame_scroll)

        name_title = ctk.CTkLabel(bottom_frame, 
                                  text="Adjust Monitors", 
                                  font=("Segoe UI", 14),
                                  height=28)#, "bold"))
        # name_title.configure(bg_color="blue")
        name_title.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        name_title.bind("<MouseWheel>", self.on_bottom_frame_scroll)







        icon = Image.open("src/assets/icons/setting_white.png")
        settings_button = ctk.CTkButton(bottom_frame, 
                                        text="", 
                                        image=ctk.CTkImage(icon), 
                                        width=1, 
                                        command=self.open_settings_window)
        settings_button.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="nse")


        # self.root.update() #////////////////////////////////////////////////
        # self.load_ui()
        # self.root.after(0, self.load_ui) #////////////////////////////////////////////////






    # MARK: load_ui()
    def load_ui(self):
        print("load_ui ------------------------------------------------")
        

        for widget in self.main_frame.winfo_children():
            widget.destroy()

        monitors_info = get_monitors_info()
        print(f"monitors_info {monitors_info}")
        print(f"monitors_info type {type(monitors_info)}")
        # monitors_info.reverse()  # Invert the order of monitors

        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

        # Сортуємо список моніторів відповідно до порядку з реєстру
        monitor_list = [serial for serial in self.monitors_order if serial in monitors_dict]
        # Додаємо монітори, яких немає в реєстрі, в кінець списку
        monitor_list += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitor_list]

        # new_window_height = 65 - 5 + 5
        new_window_height = 48 + 5 # bottom_frame height + padding
        # new_window_height += 5
        if self.main_scale_factor == 1.0:
            new_window_height += 1
            print("+1.0")
        elif self.main_scale_factor == 1.25: 
            for _ in range(len(monitors_info)):
                new_window_height += 4
            print("+1.25")
        elif self.main_scale_factor == 1.5:
            new_window_height += 5
            print("+1.5")

        for index, monitor_serial in enumerate(monitor_list):
            monitor = monitors_dict[monitor_serial]

            new_window_height += 7 # monitor_frame padx
            # new_window_height += int(7 * self.main_scale_factor)

            monitor_frame = ctk.CTkFrame(self.main_frame, 
                                        corner_radius=6, 
                                        fg_color=self.fr_color)
            # monitor_frame.configure(fg_color="green")
            monitor_frame.grid(row=index, column=0, padx=(2, 2), pady=(2, 5), sticky="ew")
            monitor_frame.columnconfigure(0, weight=1)
            
            label_frame = ctk.CTkFrame(monitor_frame, corner_radius=6)
            label_frame.configure(fg_color=self.fr_color)
            # label_frame.configure(fg_color="blue")
            label_frame.grid(row=0, column=0, padx=(2, 2), pady=(2, 0), sticky="ew")
            label_frame.columnconfigure(1, weight=1)

            monitor_label = ctk.CTkLabel(label_frame, 
                                        text=monitor["display_name"], 
                                        font=("Segoe UI", 16, "bold"))
            # monitor_label.configure(bg_color="red")
            # monitor_label.grid(row=0, column=0, padx=(5, 0), pady=(5, 5), sticky="w")
            monitor_label.grid(row=0, column=0, padx=(10, 0), pady=(5, 5), sticky="w")






            available_resolutions = monitor["AvailableResolutions"]
            sorted_resolutions = sorted(available_resolutions, key=lambda res: res[0] * res[1], reverse=True)
            formatted_resolutions = [f"{width}x{height}" for width, height in sorted_resolutions]

            # res_combobox = ctk.CTkComboBox(label_frame, values=formatted_resolutions, state="readonly", font=("Segoe UI", 14, "bold"))
            res_combobox = ctk.CTkOptionMenu(label_frame, 
                                            values=formatted_resolutions, 
                                            font=("Segoe UI", 14, "bold"))
            res_combobox.configure(command=lambda value, monitor_idx=index, frame=label_frame: self.on_resolution_select(monitor_idx, value, frame))
            res_combobox.set(monitor["Resolution"])
            # res_combobox.configure(state="disabled")
            # res_combobox.configure(bg_color="red")
            res_combobox.grid(row=0, column=1, padx=(0, 5), pady=(5, 5), sticky="e")








            if self.show_refresh_rates:  # Check the flag before displaying refresh rates
                rr_frame = ctk.CTkFrame(monitor_frame, corner_radius=6)
                rr_frame.configure(fg_color=self.fr_color)
                # rr_frame.configure(fg_color="red")
                rr_frame.grid(row=1, column=0, padx=(5, 5), pady=(2, 2), sticky="ew")
                self.update_refresh_rate_frame(monitor_serial, monitor, rr_frame)

                refresh_rates = monitor["AvailableRefreshRates"]
                refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates]
                print(f"refresh_rates {refresh_rates}")
                rows = (len(refresh_rates) + 6 - 1) // 6
                new_window_height += rows * 28 # rr_frame row
                new_window_height += 4 # rr_frame pady ############################
            # else:
            #     new_window_height -= int(4 * self.main_scale_factor)
            # new_window_height -= int(4 * self.main_scale_factor)

            br_frame = ctk.CTkFrame(monitor_frame, corner_radius=6, fg_color=self.fr_dark_color)
            # br_frame.configure(fg_color="yellow")
            br_frame.grid(row=2, column=0, padx=(2, 2), pady=(0, 2), sticky="ew")
            br_frame.columnconfigure(0, weight=1)
            br_frame.columnconfigure(1, weight=0)

            br_slider = ctk.CTkSlider(br_frame, from_=0, to=100, number_of_steps=100, height=20)

            br_level = sbc.get_brightness(display=monitor['serial'])[0]
            # br_slider.set(sbc.get_brightness(display=monitor['serial'])[0])
            br_slider.set(br_level)
            
            
            # br_slider.configure(bg_color="green")
            # br_slider.grid(row=0, column=0, padx=(3, 0), pady=(6, 6), sticky="nsew")
            br_slider.grid(row=0, column=0, padx=(3, 0), pady=(2, 2), sticky="ew")

            # br_label = ctk.CTkLabel(master=br_frame, text=int(br_slider.get()), corner_radius=6, width=50, font=("Segoe UI", 16, "bold"))
            br_label = ctk.CTkLabel(master=br_frame, 
                                    # text=int(br_slider.get()), 
                                    text=br_level, 
                                    corner_radius=6, 
                                    font=("Segoe UI", 22, "bold"), 
                                    anchor="n", 
                                    width=50, height=34)
            # br_label.configure(fg_color="blue")
            br_label.grid(row=0, column=1, padx=(0, 5), pady=(2, 2), sticky="nsew")


            # monitor_serial = monitor['serial']
            # br_slider.configure(command=lambda value, idx=index, label=br_label: self.on_br_slider_change(idx, value, label))
            br_slider.configure(command=lambda value, idx=monitor_serial, label=br_label: self.on_br_slider_change(idx, value, label))


            br_frame.bind("<MouseWheel>", command=lambda event, idx=monitor_serial, label=br_label, slider=br_slider: self.on_br_slider_scroll(event, slider, label, idx))
            br_slider.bind("<MouseWheel>", command=lambda event, idx=monitor_serial, label=br_label, slider=br_slider: self.on_br_slider_scroll(event, slider, label, idx))

            # print(f"br_level {br_slider.get()}")
            # self.brightness_values[monitor['serial']] = br_slider.get()
            self.brightness_values[monitor['serial']] = {'brightness': br_slider.get(), 'slider': br_slider, 'label': br_label}
            # print(f"self.brightness_values222222222 {self.brightness_values}")

            # monitor_frame.update_idletasks()
            # monitor_frame.update()
            # monitor_frame.after(0, monitor_frame.update())

            # new_window_height += monitor_frame.winfo_height() + 5

            # new_window_height += 84 # 38 * 2 + 4
            new_window_height += 38 * 2 + 4




            # refresh_rates = monitor["AvailableRefreshRates"]
            # print(f"refresh_rates {refresh_rates}")
            # rows = (len(refresh_rates) + 6 - 1) // 6
            # new_window_height += rows * 28

            print(f"monitor_frame {index} height = {monitor_frame.winfo_height()}")


        self.window_frame.update()
        print("self.window_frame.winfo_height()", self.window_frame.winfo_height())
        print(f"new_window_height {new_window_height}")
        self.window_height = new_window_height

        # self.y_position = self.screen_height - self.window_height - self.edge_padding - self.taskbar_height

        print("window height", self.window_height)  
        # self.y_position = int((self.screen_height - self.window_height - self.edge_padding - self.taskbar_height) * self.main_scale_factor)
        self.y_position = int((self.screen_height - self.window_height - self.edge_padding - self.taskbar_height) * self.main_scale_factor)
        print(f"x_position {self.x_position} y_position {self.y_position}")
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")
        


    


    # MARK: on_refresh_rate_btn()
    def on_refresh_rate_btn(self, monitor_serial, monitor, value, frame):
        print(f"monitor_serial {monitor_serial} value {value} frame {frame}")
        set_refresh_rate_br(monitor, value, refresh=False)

        monitors_info = get_monitors_info()
        monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}

        fresh_monitor = monitors_dict[monitor_serial]
        self.update_refresh_rate_frame(monitor_serial, fresh_monitor, frame)
        # self.load_ui()







    # MARK: update_refresh_rate_frame()
    def update_refresh_rate_frame(self, monitor_serial, monitor, frame):

        # print(f"update_refresh_rate_frame {monitor_idx} {frame}")

        for widget in frame.winfo_children():
            widget.destroy()

        # monitor = get_monitors_info()[monitor_idx]
        refresh_rates = monitor["AvailableRefreshRates"]
        # excluded_rates = read_excluded_rates_from_registry()
        refresh_rates = [rate for rate in refresh_rates if rate not in self.excluded_rates]

        if len(refresh_rates) > 6:
            num_columns = 6
        else:
            num_columns = len(refresh_rates)
        # num_columns = 6

        for i in range(num_columns):
            frame.columnconfigure(i, weight=1)

        for r_index, rate in enumerate(refresh_rates):
            rr_button = ctk.CTkButton(frame, 
                                      text=f"{rate} Hz", 
                                      font=("Segoe UI", 12), 
                                      width=1, height=24)
            

            if rate == monitor["RefreshRate"]:
                # rr_button.configure(fg_color="gray")
                pass
            else:
                rr_button.configure(border_width=1, border_color="gray", fg_color=self.fr_color)
                rr_button.configure(command=lambda rate=rate, 
                                    m_s=monitor_serial, mon=monitor, 
                                    frame=frame: self.on_refresh_rate_btn(m_s, mon, rate, frame))

            rr_button.grid(row=r_index // num_columns, 
                           column=r_index % num_columns, 
                           padx=2, pady=2, sticky="ew")
        
        print("update_refresh_rate_frame height", frame.winfo_height())



    # MARK: on_resolution_select()
    def on_resolution_select(self, monitor_idx, resolution, frame):
        print(f"on_resolution_select {resolution} idx {monitor_idx} frame {frame}")
        width, height = map(int, resolution.split('x'))
        set_resolution(get_monitors_info()[monitor_idx]["Device"], width, height)




    # MARK: on_br_slider_change()
    def on_br_slider_change(self, monitor_serial, value, label):
        # monitor_serial = get_monitors_info()[monitor_index]['serial']
        self.brightness_values[monitor_serial]['brightness'] = value
        label.configure(text=f"{int(value)}")


    def on_br_slider_scroll(self, event, slider, label, monitor_serial):
        new_value = max(0, min(100, slider.get() + (1 if event.delta > 0 else -1)))
        slider.set(new_value)
        self.brightness_values[monitor_serial]['brightness'] = new_value
        print(f"self.brightness_values type {type(self.brightness_values)}")
        label.configure(text=f"{int(new_value)}")


    # MARK: on_bottom_frame_scroll()
    def on_bottom_frame_scroll(self, event):
        print("on_bottom_frame_scroll : ", event.delta)

        for monitor_serial, monitor in self.brightness_values.items():
            brightness = monitor['brightness']
            slider = monitor['slider']
            label = monitor['label']

            new_value = max(0, min(100, slider.get() + (1 if event.delta > 0 else -1)))
            slider.set(new_value)
            self.brightness_values[monitor_serial]['brightness'] = new_value
            label.configure(text=f"{int(new_value)}")

























    # MARK: open_settings_window()
    def open_settings_window(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():

            self.settings_window = ctk.CTkToplevel(self.root)
            self.settings_window.title("MoniTune Settings")
            self.settings_window.grid_rowconfigure(0, weight=1)
            self.settings_window.grid_columnconfigure(0, weight=1)

            settings_window_width = 600
            settings_window_height = 450
            self.settings_window.geometry(f"{settings_window_width}x{settings_window_height}")

            # self.settings_window.after(250, lambda: self.settings_window.iconbitmap('icons/icon_color_dev.ico'))
            # self.settings_window.after(250, lambda: self.settings_window.iconbitmap(self.title_bar_icon))
            self.settings_window.after(250, lambda: self.settings_window.iconbitmap(self.icon_path))


            tabview = ctk.CTkTabview(self.settings_window)
            tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

            # Додаємо вкладки
            general_tab = tabview.add("General")
            refresh_rate_tab = tabview.add("Refresh Rates")
            brightness_tab = tabview.add("Brightness")
            # time_tab = tabview.add("Time adjustment")
            # hotkeys_tab = tabview.add("Hotkeys")
            about_tab = tabview.add("About")










            










            reg_order = read_order_from_registry() # ['5&19396927&5&UID256', 'H4TN602437']

            monitors_info = get_monitors_info()
            # Створюємо словник, де ключ — серійний номер
            monitors_dict = {monitor['serial']: monitor for monitor in monitors_info}
            print(f"monitors_dict {monitors_dict}")


            # Сортуємо список моніторів відповідно до порядку з реєстру
            monitor_list = [serial for serial in reg_order if serial in monitors_dict]
            print(f"monitor_list 1 {monitor_list}")
            # Додаємо монітори, яких немає в реєстрі, в кінець списку
            monitor_list += [monitor['serial'] for monitor in monitors_info if monitor['serial'] not in monitor_list]
            print(f"monitor_list 2 {monitor_list}")



            order_settings_label = ctk.CTkLabel(general_tab, text="Reorder Monitors")
            order_settings_label.pack(pady=(10, 5))

            order_frame = ctk.CTkFrame(general_tab)


            def create_monitor_list():

                # Видалити старі віджети
                for widget in order_frame.winfo_children():
                    widget.destroy()
                # monitor_labels.clear()

                # Додати нові віджети
                for i, monitor in enumerate(monitor_list):
                    row_frame = ctk.CTkFrame(order_frame)
                    row_frame.pack(fill="x", pady=2)

                    label = ctk.CTkLabel(row_frame, text=f"{monitors_dict[monitor]["display_name"]}", width=200, anchor="w")
                    label.pack(side="left", padx=5)
                    # monitor_labels.append(label)

                    up_btn = ctk.CTkButton(row_frame, text="⬆", width=30, command=lambda i=i: move_up(i))
                    up_btn.pack(side="right", padx=2)

                    down_btn = ctk.CTkButton(row_frame, text="⬇", width=30, command=lambda i=i: move_down(i))
                    down_btn.pack(side="right", padx=2)

                # # Кнопка "Зберегти порядок"
                # save_btn = ctk.CTkButton(frame, text="💾 Зберегти порядок", command=save_order)
                # save_btn.pack(pady=10)

            def move_up(index):
                if index > 0:
                    monitor_list[index], monitor_list[index - 1] = monitor_list[index - 1], monitor_list[index]
                    create_monitor_list()
                    save_order()

            def move_down(index):
                if index < len(monitor_list) - 1:
                    monitor_list[index], monitor_list[index + 1] = monitor_list[index + 1], monitor_list[index]
                    create_monitor_list()
                    save_order()

            def save_order():
                print("New monitor order:", monitor_list)
                write_order_to_registry(monitor_list)
                self.monitors_order = monitor_list
                # self.load_ui()


            
            create_monitor_list()
            order_frame.pack()














            show_refresh_rates_var = ctk.BooleanVar(value=self.show_refresh_rates)
            show_refresh_rates_checkbox = ctk.CTkSwitch(refresh_rate_tab, 
                                                        text="Show Refresh Rates", 
                                                        variable=show_refresh_rates_var, 
                                                        command=lambda: self.toggle_refresh_rates(show_refresh_rates_var))
            show_refresh_rates_checkbox.pack(pady=15, padx=15)
            



            # MARK: excluded_rates

            order_settings_label = ctk.CTkLabel(refresh_rate_tab, text="Exclude Refresh Rates")
            order_settings_label.pack(pady=10)

            all_rates = set()
            for monitor in monitors_info:
                all_rates.update(monitor['AvailableRefreshRates'])
            all_rates = sorted(all_rates)

            excluded_rates = read_excluded_rates_from_registry()

            # Створення прокручуваного фрейму
            scroll_frame = ctk.CTkScrollableFrame(refresh_rate_tab)
            scroll_frame.pack(fill="y", expand=True)

            # Функція для оновлення списку excluded
            def update_excluded(rate, value):
                print(f"Rate: {rate}, Switch: {value}")
                if value == 1:  # Якщо перемикач увімкнений
                    if rate in excluded_rates:
                        excluded_rates.remove(rate)
                else:  # Якщо перемикач вимкнений
                    if rate not in excluded_rates:
                        excluded_rates.append(rate)

                write_excluded_rates_to_registry(excluded_rates)
                self.excluded_rates = excluded_rates
                print(f"Updated excluded list: {excluded_rates}")  # Виведення оновленого списку


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




















            label_tab3 = ctk.CTkLabel(about_tab, text="about_tab", font=("Arial", 16))
            label_tab3.pack(pady=20)

        else:
            self.settings_window.focus()



    def toggle_refresh_rates(self, var):
        self.show_refresh_rates = var.get()
        # write_show_refresh_rates_to_registry(self.show_refresh_rates)
        reg_write_bool(config.REGISTRY_PATH, "ShowRefreshRates", self.show_refresh_rates)
        self.load_ui()





























    # MARK: create_tray_icon()
    def create_tray_icon(self):

        icon_image = Image.open(self.icon_path)
        # icon_image = Image.new('RGB', (64, 64), color=(255, 255, 255))

        menu = Menu(
            MenuItem("Quick access", self.on_tray_click, default=True, visible=False),
            MenuItem("Refresh displays", self.load_ui),
            MenuItem("Settings", self.open_settings_window),
            pystray.Menu.SEPARATOR,
            MenuItem("Exit", self.quit_app)
        )

        self.icon = Icon("Monitune", icon_image, f"MoniTune {"v0.0.1"}", menu)
        self.icon.run()







    # MARK: refresh_ui()
    def refresh_ui(self):
        print("refresh_ui")
        monitors_info = get_monitors_info()
        for index, monitor in enumerate(monitors_info):

            br_level = int(sbc.get_brightness(display=monitor['serial'])[0])

            monitor_frame = self.main_frame.grid_slaves(row=index, column=0)[0]
            br_frame = monitor_frame.grid_slaves(row=2, column=0)[0]
            br_slider = br_frame.grid_slaves(row=0, column=0)[0]
            # br_slider.set(sbc.get_brightness(display=monitor['serial'])[0])
            br_slider.set(br_level)

            br_label = br_frame.grid_slaves(row=0, column=1)[0]
            # br_label.configure(text=int(br_slider.get()))
            br_label.configure(text=br_level)







    # MARK: on_tray_click()
    def on_tray_click(self, icon, item):
        if not self.root.winfo_viewable():
            print("on_tray_click show")

            # monitors_info = get_monitors_info()
            # if self.prev_monitors_info != monitors_info:
            #     print("on_tray_click show load_ui")
            #     self.prev_monitors_info = monitors_info
            #     self.root.after(0, self.load_ui)
            #     # self.load_ui()
            # else:
            #     print("on_tray_click show refresh_ui")
            #     # self.refresh_ui() ##########################
            #     self.root.after(0, self.load_ui)
            # self.prev_monitors_info = monitors_info

            self.root.geometry(f"{self.window_width}x{self.window_height}+{int(self.screen_width * self.main_scale_factor)}+{self.y_position}")

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
        self.brightness_sync_thread = threading.Thread(target=self.brightness_sync, daemon=True)
        self.brightness_sync_thread.start()

        # self.animate_window_open()

    # MARK: hide_window()
    def hide_window(self):
        self.window_open = False
        # self.brightness_sync_thread.join()

        # print(self.brightness_values)
        # self.brightness_values.clear() ##################################################################
        # print(self.brightness_values)

        self.root.withdraw()

    # MARK: on_focus_out()
    def on_focus_out(self, event):
        if self.root.winfo_viewable():
            print("on_focus_out")
            self.hide_window()



    # MARK: animate_window_open()
    def animate_window_open(self, speed=20):
        
        for i in range(int(self.screen_width * self.main_scale_factor), self.x_position, -speed):
        # for i in range(self.screen_width, self.x_position, -speed):
            self.root.geometry(f"{self.window_width}x{self.window_height}+{i}+{self.y_position}")
            self.root.update()
            time.sleep(0.003)
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_position}+{self.y_position}")
    
    # MARK: animate_window_close()
    def animate_window_close(self, speed=2):
        current_x_position = self.root.winfo_x()
        for i in range(current_x_position, self.screen_width, speed):
            self.root.geometry(f"{self.window_width}x{self.window_height}+{i}+{self.y_position}")
            self.root.update()
            time.sleep(0.003)
    


    # MARK: brightness_sync()
    def brightness_sync(self):
        while self.window_open:
            # start_time = time.time()  # Start time measurement

            brightness_values_copy = self.brightness_values.copy()
            for monitor_serial, monitor in brightness_values_copy.items():
                brightness = monitor['brightness']
                current_brightness = sbc.get_brightness(display=monitor_serial)[0]
                
                if current_brightness != brightness:
                    print(f"set_brightness {monitor_serial} {brightness}")
                    set_brightness(monitor_serial, brightness)

            # print("brightness_sync")

            # end_time = time.time()  # End time measurement
            # print(f"Brightness sync took {end_time - start_time:.4f} seconds")

            time.sleep(0.25)

    

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
    else:
        # Якщо програма запущена з Python, використовуємо поточну директорію
        icon_path_s = 'src/assets/icons/icon_color_dev.ico'
        # if is_dark_theme():
        #     icon_path = 'icons/icon_light.ico' 
        # else:
        #     icon_path = 'icons/icon_dark.ico'


    app = MonitorTuneApp(icon_path_s)
    app.run()
