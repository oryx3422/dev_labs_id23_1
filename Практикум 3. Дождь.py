import pygame
import random
import json
import os
import threading
import tkinter as tk
from tkinter import ttk


def load_config():
    default_config = {
        "drop_density": 0.5,
        "min_speed": 2,
        "max_speed": 5,
        "min_angle": -1,
        "max_angle": 1,
        "cloud_count": 0,
        "cloud_size": 100
    }

    if not os.path.exists('config.json'):
        with open('config.json', 'w') as f:
            json.dump(default_config, f)
        return default_config

    with open('config.json', 'r') as f:
        config = json.load(f)

    for key, value in default_config.items():
        if key not in config:
            config[key] = value

    return config

class Drop:
    def __init__(self, x, y, speed, angle):
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle

    def update(self):
        self.x += self.speed * self.angle / 100
        self.y += self.speed

class Cloud:
    def __init__(self, x, y, size, shape_type, drop_density=0.5, min_speed=2, max_speed=5):
        self.x = x
        self.y = y
        self.size = size
        self.shape_type = shape_type
        self.drop_density = drop_density
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.is_dragged = False
        self.is_selected = False
        self.drops = []  # Капли, связанные с данной тучкой

    def draw(self, screen):
        if self.shape_type == "rectangle":
            pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.size, self.size // 2))
        elif self.shape_type == "oval":
            pygame.draw.ellipse(screen, (200, 200, 200), (self.x, self.y, self.size, self.size // 2))
        elif self.shape_type == "eight":
            pygame.draw.circle(screen, (200, 200, 200), (self.x + self.size // 2, self.y + self.size // 8),
                               self.size // 4)
            pygame.draw.circle(screen, (200, 200, 200), (self.x + 3 * self.size // 4, self.y + self.size // 4),
                               self.size // 4)

        if self.is_selected:
            pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.size, self.size // 2), 3)

    def check_click(self, pos):
        mouse_x, mouse_y = pos
        if (self.x <= mouse_x <= self.x + self.size) and (self.y <= mouse_y <= self.y + self.size // 2):
            return True
        return False

    def move(self, pos):
        if self.is_dragged:
            mouse_x, mouse_y = pos
            self.x = mouse_x - self.size // 2
            self.y = mouse_y - self.size // 4

    def edit_properties(self, size_change, drop_density_change, max_speed_change):
        self.size = max(10, int(size_change))
        self.drop_density = max(0.1, float(drop_density_change))
        self.max_speed = max(0.1, float(max_speed_change))

    def add_drops(self):
        num_drops = int(self.drop_density * 5)
        for _ in range(num_drops):
            x = random.randint(self.x, self.x + self.size)
            y = random.randint(self.y, self.y + self.size // 2)
            speed = random.uniform(self.min_speed, self.max_speed)
            angle = random.uniform(config['min_angle'], config['max_angle'])
            self.drops.append(Drop(x, y, speed, angle))

# Глобальные переменные для хранения выбранного облака и ссылок на слайдеры
selected_cloud = None
size_slider = None
density_slider = None
max_speed_slider = None
clouds = []

def run_tkinter_sliders():
    def update_size(val):
        global selected_cloud
        if selected_cloud:
            try:
                size = float(val)
                selected_cloud.edit_properties(size, selected_cloud.drop_density, selected_cloud.max_speed)
            except ValueError:
                print(f"Invalid value for size: {val}")

    def update_density(val):
        global selected_cloud
        if selected_cloud:
            try:
                drop_density = float(val)
                selected_cloud.edit_properties(selected_cloud.size, drop_density, selected_cloud.max_speed)
            except ValueError:
                print(f"Invalid value for density: {val}")

    def update_max_speed(val):
        global selected_cloud
        if selected_cloud:
            try:
                max_speed = float(val)
                selected_cloud.edit_properties(selected_cloud.size, selected_cloud.drop_density, max_speed)
            except ValueError:
                print(f"Invalid value for max speed: {val}")

    def on_size_slider_select(event):
        global selected_cloud, size_slider
        if selected_cloud:
            size_slider.set(selected_cloud.size)

    def on_density_slider_select(event):
        global selected_cloud, density_slider
        if selected_cloud:
            density_slider.set(selected_cloud.drop_density)

    def on_max_speed_slider_select(event):
        global selected_cloud, max_speed_slider
        if selected_cloud:
            max_speed_slider.set(selected_cloud.max_speed)

    root = tk.Tk()
    root.title("Cloud Controls")

    global size_slider, density_slider, max_speed_slider

    # Слайдер для размера облака (100 будет посередине)
    size_slider = ttk.Scale(root, from_=10, to=200, orient="horizontal", command=update_size)
    size_slider.set(100)  #
    size_slider.bind("<ButtonRelease-1>", on_size_slider_select)
    size_slider.pack()

    # Слайдер для плотности капель
    density_slider = ttk.Scale(root, from_=0.1, to=5.0, orient="horizontal", command=update_density)
    density_slider.bind("<ButtonRelease-1>", on_density_slider_select)
    density_slider.pack()

    # Слайдер для максимальной скорости капель, начинающийся с 0
    max_speed_slider = ttk.Scale(root, from_=0, to=10.0, orient="horizontal", command=update_max_speed)
    max_speed_slider.bind("<ButtonRelease-1>", on_max_speed_slider_select)
    max_speed_slider.pack()

    # Кнопка добавления тучки
    add_button = ttk.Button(root, text="Add Cloud", command=add_cloud)
    add_button.pack()

    # Кнопка удаления тучки
    remove_button = ttk.Button(root, text="Remove Cloud", command=remove_cloud)
    remove_button.pack()

    root.mainloop()

def add_cloud():
    global clouds, config, width, height
    shapes = ["rectangle", "oval", "eight"]
    x = random.randint(0, width - config['cloud_size'])
    y = random.randint(0, height // 2)
    shape_type = random.choice(shapes)
    new_cloud = Cloud(x, y, config['cloud_size'], shape_type,
                      drop_density=0.0,
                      min_speed=config['min_speed'],
                      max_speed=config['max_speed'])
    clouds.append(new_cloud)

def remove_cloud():
    global clouds, selected_cloud
    if clouds:
        if selected_cloud in clouds:
            clouds.remove(selected_cloud)
            selected_cloud = None
        else:
            clouds.pop()

def main():
    global selected_cloud, size_slider, density_slider, max_speed_slider, config, width, height, clouds

    pygame.init()
    config = load_config()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    clouds = []

    threading.Thread(target=run_tkinter_sliders, daemon=True).start()

    running = True
    dragging_cloud = None

    while running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for cloud in clouds:
                        if cloud.check_click(event.pos):
                            if selected_cloud == cloud:
                                cloud.is_selected = False
                                selected_cloud = None
                            else:
                                for c in clouds:
                                    c.is_selected = False
                                cloud.is_selected = True
                                selected_cloud = cloud
                                if size_slider:
                                    size_slider.set(selected_cloud.size)
                                if density_slider:
                                    density_slider.set(selected_cloud.drop_density)
                                if max_speed_slider:
                                    max_speed_slider.set(selected_cloud.max_speed)
                            dragging_cloud = cloud
                            cloud.is_dragged = True
                            break

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and dragging_cloud:
                    dragging_cloud.is_dragged = False
                    dragging_cloud = None

            if event.type == pygame.MOUSEMOTION:
                if dragging_cloud:
                    dragging_cloud.move(event.pos)

        screen.fill((230, 230, 255))

        for cloud in clouds:
            cloud.draw(screen)
            cloud.add_drops()

        for cloud in clouds:
            for drop in cloud.drops:
                drop.update()
                if drop.y > height or drop.x < 0 or drop.x > width:
                    cloud.drops.remove(drop)

        for cloud in clouds:
            for drop in cloud.drops:
                pygame.draw.line(screen, (137, 48, 225), (drop.x, drop.y), (drop.x, drop.y + 10))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
